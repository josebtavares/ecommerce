"""
Subscrições das lojas — a alternativa à comissão por venda.

- Na criação o dono escolhe 'comissao' ou 'subscricao' (+ plano). A Subscricao fica 'aguarda'
  até o admin aprovar a loja; aí arranca com o período de teste (ConfiguracaoPlataforma
  .subscricao_dias_teste) e a primeira fatura vence no fim do teste.
- Cada fatura cobre [periodo_inicio, periodo_fim). Pagar estende pago_ate até periodo_fim.
- As encomendas guardam o modelo da loja quando são feitas (Encomenda.modelo_cobranca) —
  as de subscrição não registam comissão (Comissao.registar).
Fase 2 (worker): emitir as faturas seguintes, avisos, carência e suspensão automática.
"""
import calendar
from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from ..models import ConfiguracaoPlataforma, FaturaSubscricao, Loja, PlanoSubscricao, Subscricao


def hoje():
    from .horarios import agora
    return agora().date()


def _eur(v):
    """15.5 → "15,50 €" (como no resto do site)."""
    numero = f"{v:,.2f}".replace(",", " ").replace(".", ",").replace(" ", ".")
    return f"{numero} €"


def mais_meses(d, n):
    """31/01 + 1 mês = 28/02 (ou 29); fica no último dia do mês quando o dia não existe."""
    m = d.month - 1 + n
    ano, mes = d.year + m // 12, m % 12 + 1
    return date(ano, mes, min(d.day, calendar.monthrange(ano, mes)[1]))


def _descricao(plano, inicio, fim):
    ultimo = fim - timedelta(days=1)
    return f'{plano.nome} — {inicio:%d/%m/%Y} a {ultimo:%d/%m/%Y}'


def emitir_fatura(sub, inicio, vencimento=None):
    """Fatura do período que começa em `inicio` (preço e duração do contrato da loja)."""
    fim = mais_meses(inicio, sub.meses)
    return FaturaSubscricao.objects.create(
        loja=sub.loja, subscricao=sub, plano=sub.plano, descricao=_descricao(sub.plano, inicio, fim),
        periodo_inicio=inicio, periodo_fim=fim, valor=sub.preco, vencimento=vencimento or inicio,
    )


# ── Criar / arrancar ──────────────────────────────────────────

def criar_para_loja_nova(loja, plano):
    """Na criação da loja: fica à espera da aprovação."""
    d = hoje()
    return Subscricao.objects.create(loja=loja, plano=plano, preco=plano.preco, meses=plano.meses,
                                     estado='aguarda', inicio=d, pago_ate=d)


@transaction.atomic
def arrancar(loja, com_teste=True):
    """
    Quando o admin aprova a loja (ou passa uma loja para subscrição): começa o período de teste
    (se houver) e emite a primeira fatura, que vence quando o teste acaba (ou hoje, sem teste).
    """
    sub = Subscricao.objects.select_for_update().filter(loja=loja).first()
    if not sub or sub.estado != 'aguarda':
        return sub
    d = hoje()
    dias = ConfiguracaoPlataforma.atual().subscricao_dias_teste if com_teste else 0
    sub.inicio = d
    sub.pago_ate = d + timedelta(days=dias)
    sub.teste_ate = sub.pago_ate if dias else None
    sub.estado = 'teste' if dias else 'ativa'
    sub.save(update_fields=['inicio', 'pago_ate', 'teste_ate', 'estado', 'data_atualizacao'])
    fatura = emitir_fatura(sub, sub.pago_ate)
    _avisar_fatura(fatura, nova=True)
    return sub


# ── Pagar ─────────────────────────────────────────────────────

class ErroFatura(Exception):
    pass


# motivo da suspensão automática — pagar só reactiva a loja se o motivo for este
MOTIVO_SUSPENSAO = 'Subscrição por pagar'
DIAS_AVISO = 7          # a fatura seguinte é emitida 7 dias antes do fim do período
DIAS_CARENCIA = 30      # depois do vencimento a loja continua a funcionar 30 dias


@transaction.atomic
def pagar(fatura, metodo, referencia='', notas='', quando=None):
    """Marca a fatura como paga e estende o serviço até ao fim do período (reactiva se estava suspensa)."""
    d = quando or hoje()
    fatura = FaturaSubscricao.objects.select_for_update().get(pk=fatura.pk)
    if fatura.estado != 'pendente':
        raise ErroFatura('Esta fatura já não está por pagar.')
    if metodo not in dict(FaturaSubscricao.METODOS):
        raise ErroFatura('Método de pagamento inválido.')
    fatura.estado, fatura.paga_em, fatura.metodo = 'paga', timezone.now(), metodo
    fatura.referencia, fatura.notas = referencia[:100], (notas or fatura.notas)[:300]
    fatura.save(update_fields=['estado', 'paga_em', 'metodo', 'referencia', 'notas'])

    sub = Subscricao.objects.select_for_update().get(pk=fatura.subscricao_id)
    if fatura.periodo_fim > sub.pago_ate:
        sub.pago_ate = fatura.periodo_fim
    em_divida = sub.faturas.filter(estado='pendente', vencimento__lt=d).exists()
    reativou = False
    if sub.estado in ('em_atraso', 'suspensa') and not em_divida:
        reativou = sub.estado == 'suspensa'
        sub.estado = 'ativa'
    # pagar durante o teste não o encurta: continua 'teste' até o período pago começar
    elif sub.estado == 'teste' and d >= fatura.periodo_inicio:
        sub.estado = 'ativa'
    sub.save(update_fields=['pago_ate', 'estado', 'data_atualizacao'])

    # a loja só volta se foi suspensa por causa da subscrição (não mexe numa suspensão do admin)
    loja = Loja.objects.get(pk=fatura.loja_id)
    if reativou and loja.estado == 'suspensa' and loja.estado_motivo.startswith(MOTIVO_SUSPENSAO):
        loja.mudar_estado('ativa')

    from ..Views.notificacaoView import notificar_staff, notificar_admins
    notificar_staff(loja=fatura.loja, roles=['dono'], tipo='subscricao_paga',
                    titulo=f'Subscrição paga — {fatura.descricao}',
                    mensagem=f'{_eur(fatura.valor)} recebidos. Pago até {sub.pago_ate - timedelta(days=1):%d/%m/%Y}.'
                             + (' A loja foi reactivada.' if reativou else ''),
                    link=f'/loja/{fatura.loja_id}/backoffice')
    notificar_admins(tipo='subscricao_paga', titulo=f'Subscrição paga — {fatura.loja.nome}',
                     mensagem=f'Fatura #{fatura.id} · {_eur(fatura.valor)} · {fatura.get_metodo_display()}.',
                     loja=fatura.loja, link='/admin')
    return fatura


def _avisar_fatura(fatura, nova=False):
    from ..Views.notificacaoView import notificar_staff
    notificar_staff(loja=fatura.loja, roles=['dono'], tipo='subscricao_fatura',
                    titulo=f'Nova fatura da subscrição — {_eur(fatura.valor)}' if nova else f'Fatura por pagar — {_eur(fatura.valor)}',
                    mensagem=f'{fatura.descricao}. Vence a {fatura.vencimento:%d/%m/%Y}.',
                    link=f'/loja/{fatura.loja_id}/backoffice')


# ── Mudar o modelo (admin) ────────────────────────────────────

@transaction.atomic
def mudar_modelo(loja, modelo, plano=None):
    """
    O admin força o modelo de uma loja. Para subscrição: (re)começa sem período de teste, com a
    primeira fatura a vencer hoje. Para comissão: a subscrição fica cancelada e as faturas por
    pagar anuladas (não se apagam). As encomendas já feitas mantêm o modelo que tinham.
    """
    loja = Loja.objects.select_for_update().get(pk=loja.pk)
    sub = Subscricao.objects.select_for_update().filter(loja=loja).first()
    if modelo == 'subscricao':
        if plano is None:
            raise ErroFatura('Escolhe o plano.')
        if sub and sub.estado != 'cancelada' and loja.modelo_cobranca == 'subscricao':
            raise ErroFatura('A loja já está em subscrição.')
        d = hoje()
        if sub:
            sub.plano, sub.preco, sub.meses = plano, plano.preco, plano.meses
            sub.estado, sub.inicio, sub.pago_ate, sub.teste_ate = 'aguarda', d, d, None
            sub.save()
        else:
            sub = Subscricao.objects.create(loja=loja, plano=plano, preco=plano.preco, meses=plano.meses,
                                            estado='aguarda', inicio=d, pago_ate=d)
        loja.modelo_cobranca = 'subscricao'
        loja.save(update_fields=['modelo_cobranca', 'data_atualizacao'])
        if loja.estado == 'ativa':
            arrancar(loja, com_teste=False)
    elif modelo == 'comissao':
        if loja.modelo_cobranca == 'comissao':
            raise ErroFatura('A loja já está em comissão.')
        if sub:
            sub.estado = 'cancelada'
            sub.save(update_fields=['estado', 'data_atualizacao'])
            sub.faturas.filter(estado='pendente').update(estado='anulada', notas='Anulada: a loja passou para comissão.')
        loja.modelo_cobranca = 'comissao'
        loja.save(update_fields=['modelo_cobranca', 'data_atualizacao'])
    else:
        raise ErroFatura('Modelo inválido.')
    return loja


# ── Payloads ──────────────────────────────────────────────────

def plano_payload(p):
    return {'id': p.id, 'nome': p.nome, 'periodicidade': p.periodicidade, 'periodicidade_nome': p.get_periodicidade_display(),
            'meses': p.meses, 'preco': str(p.preco), 'preco_mes': str((p.preco / p.meses).quantize(Decimal('0.01'))),
            'descricao': p.descricao, 'ativo': p.ativo, 'ordem': p.ordem}


def fatura_payload(f):
    return {'id': f.id, 'descricao': f.descricao, 'periodo_inicio': f.periodo_inicio.isoformat(),
            'periodo_fim': (f.periodo_fim - timedelta(days=1)).isoformat(), 'valor': str(f.valor),
            'estado': f.estado, 'estado_nome': f.get_estado_display(), 'vencimento': f.vencimento.isoformat(),
            'atrasada': f.estado == 'pendente' and f.vencimento < hoje(),
            'paga_em': f.paga_em.isoformat() if f.paga_em else None, 'metodo': f.metodo,
            'metodo_nome': f.get_metodo_display() if f.metodo else '', 'notas': f.notas, 'loja_id': f.loja_id}


def subscricao_payload(sub):
    if not sub:
        return None
    return {'id': sub.id, 'plano': plano_payload(sub.plano), 'preco': str(sub.preco), 'meses': sub.meses,
            'estado': sub.estado, 'estado_nome': sub.get_estado_display(), 'inicio': sub.inicio.isoformat(),
            # último dia pago (pago_ate é o dia em que deixa de estar)
            'pago_ate': (sub.pago_ate - timedelta(days=1)).isoformat() if sub.pago_ate > sub.inicio else None,
            'teste_ate': (sub.teste_ate - timedelta(days=1)).isoformat() if sub.teste_ate else None,
            'auto_renovar': sub.auto_renovar}


def planos_ativos():
    return list(PlanoSubscricao.objects.filter(ativo=True))


# ── Ciclo automático (worker: processar_videos, a cada 10 minutos) ───────────

def _marcar(fatura, chave):
    """True se o aviso `chave` ainda não tinha sido dado (e regista-o)."""
    if chave in (fatura.avisos or []):
        return False
    fatura.avisos = [*(fatura.avisos or []), chave]
    fatura.save(update_fields=['avisos'])
    return True


def _avisar_dono(loja, titulo, mensagem):
    from ..Views.notificacaoView import notificar_staff
    notificar_staff(loja=loja, roles=['dono'], tipo='subscricao_fatura', titulo=titulo, mensagem=mensagem,
                    link=f'/loja/{loja.id}/backoffice')


def _avisar_admins(loja, titulo, mensagem):
    from ..Views.notificacaoView import notificar_admins
    notificar_admins(tipo='subscricao_fatura', titulo=titulo, mensagem=mensagem, loja=loja, link='/admin')


def suspensao_em(fatura):
    """Dia em que a loja é suspensa se esta fatura não for paga."""
    return fatura.vencimento + timedelta(days=DIAS_CARENCIA)


def processar(quando=None):
    """
    Uma volta do ciclo para todas as subscrições activas. Idempotente: os avisos ficam
    registados na fatura (FaturaSubscricao.avisos) e cada passo só acontece uma vez.
      1. fim do teste → 'ativa'
      2. fatura do período seguinte emitida 7 dias antes (ao preço actual do plano)
      3. avisos 3 dias antes e no dia
      4. no dia: pagamento automático (simulado) se estiver ligado
      5. depois do vencimento: 'em_atraso' + avisos aos 7, 14, 21 e 28 dias
      6. 30 dias depois do vencimento: loja suspensa (MOTIVO_SUSPENSAO)
    Devolve um resumo {'emitidas', 'pagas_auto', 'em_atraso', 'suspensas'}.
    """
    d = quando or hoje()
    resumo = {'emitidas': 0, 'pagas_auto': 0, 'em_atraso': 0, 'suspensas': 0}
    subs_qs = (Subscricao.objects.select_related('loja', 'plano')
               .filter(estado__in=['teste', 'ativa', 'em_atraso'], loja__modelo_cobranca='subscricao'))
    for sub in subs_qs:
        try:
            with transaction.atomic():
                _processar_uma(Subscricao.objects.select_for_update().select_related('loja', 'plano').get(pk=sub.pk), d, resumo)
        except Exception as e:          # uma loja com problemas não pára as outras
            import logging
            logging.getLogger(__name__).exception('subscrição %s: %s', sub.pk, e)
    return resumo


def _processar_uma(sub, d, resumo):
    loja = sub.loja
    if loja.estado not in ('ativa', 'fechada'):
        return

    # 1. fim do teste
    if sub.estado == 'teste' and sub.teste_ate and d >= sub.teste_ate:
        sub.estado = 'ativa'
        sub.save(update_fields=['estado', 'data_atualizacao'])

    # 2. fatura do período seguinte, 7 dias antes de o período pago acabar
    tem_seguinte = sub.faturas.filter(periodo_inicio=sub.pago_ate).exclude(estado='anulada').exists()
    if not tem_seguinte and d >= sub.pago_ate - timedelta(days=DIAS_AVISO):
        if sub.preco != sub.plano.preco or sub.meses != sub.plano.meses:      # renova ao preço actual do plano
            sub.preco, sub.meses = sub.plano.preco, sub.plano.meses
            sub.save(update_fields=['preco', 'meses', 'data_atualizacao'])
        f = emitir_fatura(sub, sub.pago_ate)
        _marcar(f, 'emitida')
        _avisar_fatura(f, nova=True)
        resumo['emitidas'] += 1

    for f in sub.faturas.filter(estado='pendente').order_by('vencimento'):
        falta = (f.vencimento - d).days
        # 3. lembretes
        if falta == 3 and _marcar(f, 'd3'):
            _avisar_dono(loja, f'A fatura da subscrição vence daqui a 3 dias — {_eur(f.valor)}',
                         f'{f.descricao}. Vence a {f.vencimento:%d/%m/%Y}.')
        # 4. no dia (ou depois, se o worker esteve parado): pagamento automático
        if falta <= 0 and sub.auto_renovar and 'auto' not in (f.avisos or []):
            _marcar(f, 'auto')
            pagar(f, 'simulado', referencia=f'AUTO-{f.id}', notas='Pagamento automático', quando=d)
            resumo['pagas_auto'] += 1
            sub.refresh_from_db()
            continue
        if falta == 0 and _marcar(f, 'd0'):
            _avisar_dono(loja, f'A fatura da subscrição vence hoje — {_eur(f.valor)}',
                         f'{f.descricao}. Paga hoje em Backoffice → Subscrição.')
        if falta >= 0:
            continue

        # 5. em atraso
        atraso = -falta
        limite = suspensao_em(f)
        if sub.estado != 'em_atraso' and sub.estado != 'suspensa':
            sub.estado = 'em_atraso'
            sub.save(update_fields=['estado', 'data_atualizacao'])
            resumo['em_atraso'] += 1
        if _marcar(f, 'atraso'):
            _avisar_dono(loja, f'Subscrição em atraso — {_eur(f.valor)}',
                         f'{f.descricao} venceu a {f.vencimento:%d/%m/%Y}. Se não for paga, a loja é suspensa a {limite:%d/%m/%Y}.')
            _avisar_admins(loja, f'Subscrição em atraso — {loja.nome}', f'Fatura #{f.id} · {_eur(f.valor)} · venceu a {f.vencimento:%d/%m/%Y}.')
        for dias in (7, 14, 21, 28):
            if atraso >= dias and atraso < DIAS_CARENCIA and _marcar(f, f'a{dias}'):
                faltam = (limite - d).days
                _avisar_dono(loja, f'Subscrição em atraso há {dias} dias — {_eur(f.valor)}',
                             f'Faltam {faltam} dia(s): a loja é suspensa a {limite:%d/%m/%Y} se a fatura não for paga.')

        # 6. fim da carência → suspensa
        if d >= limite and _marcar(f, 'suspensa'):
            sub.estado = 'suspensa'
            sub.save(update_fields=['estado', 'data_atualizacao'])
            if loja.estado == 'ativa':
                loja.mudar_estado('suspensa', f'{MOTIVO_SUSPENSAO} (fatura #{f.id}, {_eur(f.valor)}).')
            _avisar_dono(loja, 'A loja foi suspensa — subscrição por pagar',
                         f'A fatura de {_eur(f.valor)} venceu a {f.vencimento:%d/%m/%Y}. Paga em Backoffice → Subscrição e a loja volta logo.')
            _avisar_admins(loja, f'Loja suspensa automaticamente — {loja.nome}',
                           f'Subscrição por pagar: fatura #{f.id}, {_eur(f.valor)}, vencida a {f.vencimento:%d/%m/%Y}.')
            resumo['suspensas'] += 1
            break


def aviso_loja(sub, pendentes, quando=None):
    """
    A faixa do backoffice: None, ou {'tipo': 'suspensa'|'atraso'|'vence', 'texto', 'suspensao_em'}.
    `pendentes` = faturas por pagar da loja.
    """
    if not sub or sub.estado in ('aguarda', 'cancelada'):
        return None
    d = quando or hoje()
    pend = sorted(pendentes, key=lambda f: f.vencimento)
    if sub.estado == 'suspensa':
        return {'tipo': 'suspensa', 'suspensao_em': None,
                'texto': 'A loja está suspensa porque a subscrição não foi paga. Paga a fatura e a loja volta logo.'}
    vencidas = [f for f in pend if f.vencimento < d]
    if vencidas:
        limite = suspensao_em(vencidas[0])
        return {'tipo': 'atraso', 'suspensao_em': limite.isoformat(),
                'texto': f'Subscrição em atraso ({_eur(sum(f.valor for f in vencidas))}). Paga até {limite - timedelta(days=1):%d/%m/%Y} '
                         f'— a {limite:%d/%m/%Y} a loja é suspensa.'}
    breve = [f for f in pend if (f.vencimento - d).days <= 3]
    if breve and not sub.auto_renovar:
        f = breve[0]
        quando_txt = 'hoje' if f.vencimento == d else f'a {f.vencimento:%d/%m/%Y}'
        return {'tipo': 'vence', 'suspensao_em': None, 'texto': f'A fatura da subscrição ({_eur(f.valor)}) vence {quando_txt}.'}
    return None
