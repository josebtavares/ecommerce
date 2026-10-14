"""
Subscrições dos POS — o POS paga sempre subscrição (as vendas no balcão não pagam comissão).
As peças comuns (faturas, pagar, avisos, acções do admin) estão em utils/subscricoes.py.

- Uma conta tem um POS; a equipa do POS (membros) não paga nada à parte.
- POS novo: escolhe o plano ao ser criado e tem o período de teste das Definições
  (ConfiguracaoPlataforma.subscricao_dias_teste). Sem planos de POS criados, fica sem plano
  durante o teste e escolhe-o depois.
- POS que já existiam antes das subscrições: 1 mês grátis (sem plano) a contar de quando a
  subscrição é criada (garantir) — escolhem o plano durante esse mês.
- A primeira fatura é emitida pelo ciclo 7 dias antes do fim do teste (nunca na criação: um
  POS sem faturas pode ser apagado com a conta).
"""
from datetime import timedelta

from django.db import IntegrityError, transaction

from ..models import ConfiguracaoPlataforma, Subscricao
from . import subscricoes as subs
from .subscricoes import ErroFatura, _eur, hoje, mais_meses

MESES_GRATIS_EXISTENTES = 1


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


def criar_para_pos_novo(pos, plano):
    """POS acabado de criar: período de teste com o plano escolhido (ou sem plano, se não há planos)."""
    dias = ConfiguracaoPlataforma.atual().subscricao_dias_teste
    sub = _criar(pos, plano, dias=dias)
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
      a primeira fatura é emitida já, a vencer hoje.
    - Com plano: igual às lojas — vale a partir da renovação (ou substitui já a renovação por pagar).
    """
    sub = Subscricao.objects.select_for_update().filter(pos=pos).first()
    if not sub or sub.estado == 'cancelada':
        raise ErroFatura('Este POS não tem subscrição.')
    if plano.tipo != 'pos':
        raise ErroFatura('Escolhe um plano de POS.')
    if sub.plano_id:
        return subs.mudar_plano_sub(sub, plano)
    sub.plano, sub.preco, sub.meses = plano, plano.preco, plano.meses
    sub.save(update_fields=['plano', 'preco', 'meses', 'data_atualizacao'])
    d = hoje()
    if d >= sub.pago_ate and not sub.faturas.filter(periodo_inicio__gte=sub.pago_ate).exclude(estado='anulada').exists():
        # o período grátis acabou sem plano: a fatura começa hoje (não se cobra o tempo sem plano)
        sub.pago_ate = d
        sub.save(update_fields=['pago_ate', 'data_atualizacao'])
        f = subs.emitir_fatura(sub, d)
        subs._marcar(f, 'emitida')
        if f.estado == 'pendente':
            subs._avisar_fatura(f, nova=True)
        sub.refresh_from_db()
        return sub, f
    return sub, None


def aviso_pos(sub, pendentes, quando=None):
    """
    A faixa do painel do POS: None ou {'tipo': 'sem_plano'|'suspensa'|'atraso'|'vence', 'texto', 'suspensao_em'}.
    """
    if not sub or sub.estado == 'cancelada':
        return None
    d = quando or hoje()
    if sub.estado == 'suspensa':
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
