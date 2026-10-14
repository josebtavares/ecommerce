"""
Subscrições dos POS — o POS paga sempre subscrição (as vendas no balcão não pagam comissão).
As peças comuns (faturas, pagar, avisos, acções do admin, ciclo) estão em utils/subscricoes.py.

- Uma conta tem um POS; a equipa do POS (membros) não paga nada à parte.
- POS novo: escolhe o plano ao ser criado e tem o período de teste das Definições
  (ConfiguracaoPlataforma.subscricao_dias_teste). Sem planos de POS criados, fica sem plano
  durante o teste e escolhe-o depois.
- POS que já existiam antes das subscrições: 1 mês grátis (sem plano) a contar de quando a
  subscrição é criada (garantir) — escolhem o plano durante esse mês.
- A primeira fatura é emitida pelo ciclo 7 dias antes do fim do teste (nunca na criação: um
  POS sem faturas pode ser apagado com a conta).
- O período grátis acaba sem plano → conta como atraso: 30 dias para escolher e pagar, depois
  o POS é suspenso (avisos em Subscricao.avisos, 'sp_…').
- Plano Loja + POS: a loja (em subscrição) paga um plano que inclui o POS ligado a ela. Enquanto
  isso, o POS não tem faturas próprias (Subscricao.coberta_por); se a loja não paga e é suspensa,
  o POS vai com ela. Quando deixa de estar incluído (desligou-se da loja, a loja mudou de plano
  ou passou a comissão), o POS tem 30 dias até precisar do seu plano.
"""
from datetime import timedelta

from django.db import IntegrityError, transaction

from ..models import ConfiguracaoPlataforma, Subscricao
from . import subscricoes as subs
from .subscricoes import ErroFatura, _eur, hoje, mais_meses

MESES_GRATIS_EXISTENTES = 1
DIAS_APOS_COBERTURA = 30          # sai do plano Loja + POS → 30 dias até pagar o próprio plano


def _criar(pos, plano, dias=None, meses=None):
    """Cria a subscrição em período de teste (dias ou meses). Devolve a existente se já houver."""
    d = hoje()
    fim = mais_meses(d, meses) if meses else d + timedelta(days=dias or 0)
    try:
        with transaction.atomic():
            return Subscricao.objects.create(
                pos=pos, plano=plano, preco=plano.preco if plano else 0, meses=plano.meses if plano else 1,
                estado='teste' if fim > d else 'ativa', inicio=d, pago_ate=fim, teste_ate=fim if fim > d else None)
    except IntegrityError:                    # outro pedido criou-a ao mesmo tempo
        return Subscricao.objects.get(pos=pos)


def garantir(pos):
    """A subscrição do POS; um POS de antes das subscrições recebe aqui o mês grátis."""
    sub = Subscricao.objects.filter(pos=pos).first()
    return sub or _criar(pos, None, meses=MESES_GRATIS_EXISTENTES)


def garantir_todos():
    """Dá o mês grátis a todos os POS que ainda não têm subscrição (worker). Devolve quantos."""
    from ..pos.models import ConfiguracaoPOS
    n = 0
    for pos in ConfiguracaoPOS.objects.filter(subscricao__isnull=True):
        garantir(pos)
        n += 1
    return n


@transaction.atomic
def criar_para_pos_novo(pos, plano):
    """POS acabado de criar: período de teste com o plano escolhido (ou sem plano, se não há planos)."""
    dias = ConfiguracaoPlataforma.atual().subscricao_dias_teste
    sub = _criar(pos, plano, dias=dias)
    if sincronizar(Subscricao.objects.select_for_update().get(pk=sub.pk)):
        return sub                            # ligado a uma loja com o plano Loja + POS
    if sub.estado == 'ativa' and plano:       # sem teste: a primeira fatura vence hoje
        f = subs.emitir_fatura(sub, sub.inicio)
        subs._marcar(f, 'emitida')
        if f.estado == 'pendente':
            subs._avisar_fatura(f, nova=True)
    return sub


@transaction.atomic
def escolher_plano(pos, plano):
    """
    O dono escolhe (ou muda) o plano do POS.
    - Sem plano (mês grátis / teste sem planos): fica com este. Se o período grátis já acabou,
      a primeira fatura é emitida já — começa hoje, mas vence no fim do período grátis (escolher
      o plano não dá mais prazo: a suspensão continua a ser 30 dias depois).
    - Com plano: igual às lojas — vale a partir da renovação (ou substitui já a renovação por pagar).
    """
    sub = Subscricao.objects.select_for_update().filter(pos=pos).first()
    if not sub or sub.estado == 'cancelada':
        raise ErroFatura('Este POS não tem subscrição.')
    if plano.tipo != 'pos':
        raise ErroFatura('Escolhe um plano de POS.')
    if sincronizar(sub):
        raise ErroFatura('O POS está incluído no plano Loja + POS da loja — não precisa de plano próprio.')
    if sub.plano_id:
        return subs.mudar_plano_sub(sub, plano)
    sub.plano, sub.preco, sub.meses = plano, plano.preco, plano.meses
    sub.save(update_fields=['plano', 'preco', 'meses', 'data_atualizacao'])
    d = hoje()
    if d >= sub.pago_ate and not sub.faturas.filter(periodo_inicio__gte=sub.pago_ate).exclude(estado='anulada').exists():
        # o período grátis acabou sem plano: a fatura começa hoje (não se cobra o tempo sem plano)
        vencimento = sub.pago_ate
        sub.pago_ate = d
        sub.save(update_fields=['pago_ate', 'data_atualizacao'])
        f = subs.emitir_fatura(sub, d, vencimento=vencimento)
        if f.estado == 'pendente':
            # os avisos de atraso que já passaram não chegam todos de uma vez (já os teve sem plano)
            atraso = (d - vencimento).days
            f.avisos = ['emitida'] + (['atraso', *[f'a{n}' for n in (7, 14, 21, 28) if atraso >= n]] if atraso > 0 else [])
            f.save(update_fields=['avisos'])
            subs._avisar_fatura(f, nova=True)
        subs._reavaliar(sub, d)
        sub.refresh_from_db()
        return sub, f
    return sub, None


# ── Plano Loja + POS ──────────────────────────────────────────

def loja_cobre_pos(sub_loja):
    """A subscrição desta loja inclui o POS ligado (plano Loja + POS do período em curso)?"""
    if not sub_loja or not sub_loja.loja_id or sub_loja.estado not in ('teste', 'ativa', 'em_atraso', 'suspensa'):
        return False
    if sub_loja.loja.modelo_cobranca != 'subscricao':
        return False
    plano = subs.plano_em_curso(sub_loja) or sub_loja.plano
    return bool(plano) and plano.tipo == 'loja_pos'


def cobertura(pos):
    """A subscrição da loja que inclui este POS, ou None."""
    if not pos.loja_vinculada_id:
        return None
    sub = Subscricao.objects.select_related('loja', 'plano').filter(loja_id=pos.loja_vinculada_id).first()
    if sub and sub.loja.dono_id == pos.dono_id and loja_cobre_pos(sub):
        return sub
    return None


def sincronizar(sub, d=None):
    """
    Acerta a subscrição do POS (bloqueada) com a da loja ligada. Devolve a da loja se o POS está
    incluído no plano dela, ou None.
    - passa a estar incluído: as faturas por pagar do POS são anuladas e uma suspensão por falta
      de pagamento é levantada;
    - a loja foi suspensa por não pagar → o POS também; volta quando a loja paga;
    - deixa de estar incluído: 30 dias (pelo menos) até precisar do seu plano.
    """
    from ..pos.models import ConfiguracaoPOS
    d = d or hoje()
    pos = ConfiguracaoPOS.objects.select_related('loja_vinculada').get(pk=sub.pos_id)
    cob = cobertura(pos)
    if cob:
        if sub.coberta_por_id != cob.id:
            sub.faturas.filter(estado='pendente').update(
                estado='anulada', notas=f'Anulada: o POS passou a estar incluído no plano da loja {cob.loja.nome}.')
            sub.coberta_por, sub.avisos, sub.plano_seguinte = cob, [], None
            if sub.estado in ('em_atraso', 'suspensa'):
                sub.estado = 'teste' if (sub.teste_ate and d < sub.teste_ate) else 'ativa'
            sub.save()
            subs._avisar_dono(pos, f'O POS está incluído no plano da loja {cob.loja.nome}',
                              f'O plano {(subs.plano_em_curso(cob) or cob.plano).nome} cobre a loja e o POS — não pagas o POS à parte.')
        if cob.estado == 'suspensa':
            subs.suspender(pos, f'{subs.MOTIVO_SUSPENSAO} (plano Loja + POS da loja {cob.loja.nome}).')
        else:
            subs.reativar_pos(pos)
        return cob
    if sub.coberta_por_id:
        loja_antes = sub.coberta_por.loja.nome if sub.coberta_por and sub.coberta_por.loja_id else 'a loja'
        sub.coberta_por, sub.avisos = None, []
        sub.pago_ate = max(sub.pago_ate, d + timedelta(days=DIAS_APOS_COBERTURA))
        sub.estado = 'teste' if (sub.teste_ate and d < sub.teste_ate) else 'ativa'
        sub.save()
        subs.reativar_pos(pos)
        ultimo = sub.pago_ate - timedelta(days=1)
        subs._avisar_dono(pos, 'O POS deixou de estar incluído no plano da loja',
                          f'O POS já não faz parte do plano da loja {loja_antes}. Continua grátis até {ultimo:%d/%m/%Y}'
                          + (f' — depois passas a pagar o plano {sub.plano.nome}.' if sub.plano_id
                             else ' — escolhe um plano em POS → Subscrição.'))
    return None


@transaction.atomic
def sincronizar_pos_da_loja(loja_id):
    """Depois de a loja mudar (pagou, foi suspensa, mudou de modelo): acerta os POS ligados."""
    pks = Subscricao.objects.filter(pos__loja_vinculada_id=loja_id).values_list('pk', flat=True)
    # e os que estavam incluídos nesta loja mas entretanto se desligaram
    pks = {*pks, *Subscricao.objects.filter(coberta_por__loja_id=loja_id).values_list('pk', flat=True)}
    for pk in sorted(pks):
        sincronizar(Subscricao.objects.select_for_update().get(pk=pk))


def sincronizar_pos(pos):
    """Depois de ligar / desligar o POS de uma loja."""
    with transaction.atomic():
        sub = Subscricao.objects.select_for_update().filter(pos=pos).first()
        if sub:
            sincronizar(sub)


# ── Ciclo (subscricoes.processar) ─────────────────────────────

def processar_pos(sub, d, resumo):
    """Uma volta do ciclo para a subscrição de um POS (já bloqueada)."""
    if sincronizar(sub, d):
        return                               # incluído no plano da loja: não tem faturas próprias
    pos = sub.pos
    pos.refresh_from_db()
    if sub.estado == 'suspensa' or pos.suspenso:
        return                               # suspenso: só volta pagando (ou pelo admin)
    if not sub.plano_id:
        _sem_plano(sub, pos, d, resumo)
        return
    subs.ciclo_faturas(sub, pos, d, resumo)


def _marcar_sub(sub, chave):
    if chave in (sub.avisos or []):
        return False
    sub.avisos = [*(sub.avisos or []), chave]
    sub.save(update_fields=['avisos'])
    return True


def _sem_plano(sub, pos, d, resumo):
    """Período grátis sem plano: lembretes antes de acabar; depois, atraso e suspensão como uma fatura."""
    fim = sub.pago_ate                       # o primeiro dia já não grátis
    falta = (fim - d).days
    ultimo = fim - timedelta(days=1)
    if 3 < falta <= 7 and _marcar_sub(sub, 'sp_d7') or 0 < falta <= 3 and _marcar_sub(sub, 'sp_d3'):
        subs._avisar_dono(pos, f'O período grátis do POS acaba daqui a {falta} dia(s)',
                          f'Escolhe um plano em POS → Subscrição até {ultimo:%d/%m/%Y} para continuar a usar o POS.')
    if falta > 0:
        return
    limite = fim + timedelta(days=subs.DIAS_CARENCIA)
    if sub.estado in ('teste', 'ativa'):
        sub.estado = 'em_atraso'
        sub.save(update_fields=['estado', 'data_atualizacao'])
        resumo['em_atraso'] += 1
    if _marcar_sub(sub, 'sp_fim'):
        subs._avisar_dono(pos, 'O período grátis do POS acabou',
                          f'Escolhe um plano em POS → Subscrição. Sem plano, o POS é suspenso a {limite:%d/%m/%Y}.')
        subs._avisar_admins(pos, f'POS sem plano — {subs.nome_alvo(pos)}',
                            f'O período grátis acabou a {ultimo:%d/%m/%Y} sem plano escolhido. Suspensão a {limite:%d/%m/%Y}.')
    atraso = -falta
    for dias in (7, 14, 21, 28):
        if dias <= atraso < subs.DIAS_CARENCIA and _marcar_sub(sub, f'sp_a{dias}'):
            subs._avisar_dono(pos, f'O POS está sem plano há {dias} dias',
                              f'Faltam {(limite - d).days} dia(s): escolhe um plano até {limite - timedelta(days=1):%d/%m/%Y} '
                              f'ou o POS é suspenso.')
    if d >= limite and _marcar_sub(sub, 'sp_suspensa'):
        sub.estado = 'suspensa'
        sub.save(update_fields=['estado', 'data_atualizacao'])
        subs.suspender(pos, f'{subs.MOTIVO_SUSPENSAO} (o período grátis acabou sem plano).')
        subs._avisar_dono(pos, 'O POS foi suspenso — sem plano',
                          'O período grátis acabou e não foi escolhido um plano. Escolhe um plano em POS → Subscrição, '
                          'paga a primeira fatura e o POS volta logo.')
        subs._avisar_admins(pos, f'POS suspenso automaticamente — {subs.nome_alvo(pos)}',
                            f'Sem plano desde {fim:%d/%m/%Y}.')
        resumo['suspensas'] += 1


# ── Faixa do painel ───────────────────────────────────────────

def aviso_pos(sub, pendentes, quando=None, cob=None):
    """
    A faixa do painel do POS: None ou {'tipo': 'sem_plano'|'suspensa'|'atraso'|'vence', 'texto', 'suspensao_em'}.
    `cob` = a subscrição da loja quando o POS está incluído no plano dela.
    """
    if not sub or sub.estado == 'cancelada':
        return None
    d = quando or hoje()
    if cob:
        if cob.estado == 'suspensa':
            return {'tipo': 'suspensa', 'suspensao_em': None,
                    'texto': f'O POS está suspenso porque a subscrição da loja {cob.loja.nome} (plano Loja + POS) '
                             f'não foi paga. Paga no backoffice da loja e o POS volta logo.'}
        return None
    if sub.estado == 'suspensa':
        if not sub.plano_id:
            return {'tipo': 'suspensa', 'suspensao_em': None,
                    'texto': 'O POS está suspenso porque o período grátis acabou sem plano. Escolhe um plano, '
                             'paga a primeira fatura e o POS volta logo.'}
        return {'tipo': 'suspensa', 'suspensao_em': None,
                'texto': 'O POS está suspenso porque a subscrição não foi paga. Paga a fatura e o POS volta logo.'}
    if not sub.plano_id:
        ultimo = sub.pago_ate - timedelta(days=1)
        if d < sub.pago_ate:
            return {'tipo': 'sem_plano', 'suspensao_em': None,
                    'texto': f'Tens o POS grátis até {ultimo:%d/%m/%Y}. Escolhe um plano para continuar a usá-lo depois.'}
        limite = sub.pago_ate + timedelta(days=subs.DIAS_CARENCIA)
        return {'tipo': 'atraso', 'suspensao_em': limite.isoformat(),
                'texto': f'O período grátis acabou a {ultimo:%d/%m/%Y}. Escolhe um plano até '
                         f'{limite - timedelta(days=1):%d/%m/%Y} — a {limite:%d/%m/%Y} o POS é suspenso.'}
    pend = sorted(pendentes, key=lambda f: f.vencimento)
    vencidas = [f for f in pend if f.vencimento < d]
    if vencidas:
        limite = subs.suspensao_em(vencidas[0])
        return {'tipo': 'atraso', 'suspensao_em': limite.isoformat(),
                'texto': f'Subscrição em atraso ({_eur(sum(f.valor for f in vencidas))}). Paga até {limite - timedelta(days=1):%d/%m/%Y} '
                         f'— a {limite:%d/%m/%Y} o POS é suspenso.'}
    breve = [f for f in pend if (f.vencimento - d).days <= 3]
    if breve and not sub.auto_renovar:
        f = breve[0]
        quando_txt = 'hoje' if f.vencimento == d else f'a {f.vencimento:%d/%m/%Y}'
        return {'tipo': 'vence', 'suspensao_em': None, 'texto': f'A fatura da subscrição ({_eur(f.valor)}) vence {quando_txt}.'}
    return None
