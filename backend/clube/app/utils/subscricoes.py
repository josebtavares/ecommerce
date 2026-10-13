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


@transaction.atomic
def pagar(fatura, metodo, referencia='', notas=''):
    """Marca a fatura como paga e estende o serviço até ao fim do período."""
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
    # pagar durante o teste não o encurta: continua 'teste' até o período pago começar
    if sub.estado == 'em_atraso' or (sub.estado == 'teste' and hoje() >= fatura.periodo_inicio):
        sub.estado = 'ativa'
    sub.save(update_fields=['pago_ate', 'estado', 'data_atualizacao'])

    from ..Views.notificacaoView import notificar_staff, notificar_admins
    notificar_staff(loja=fatura.loja, roles=['dono'], tipo='subscricao_paga',
                    titulo=f'Subscrição paga — {fatura.descricao}',
                    mensagem=f'€{fatura.valor} recebidos. Pago até {sub.pago_ate - timedelta(days=1):%d/%m/%Y}.',
                    link=f'/loja/{fatura.loja_id}/backoffice')
    notificar_admins(tipo='subscricao_paga', titulo=f'Subscrição paga — {fatura.loja.nome}',
                     mensagem=f'Fatura #{fatura.id} · €{fatura.valor} · {fatura.get_metodo_display()}.',
                     loja=fatura.loja, link='/admin')
    return fatura


def _avisar_fatura(fatura, nova=False):
    from ..Views.notificacaoView import notificar_staff
    notificar_staff(loja=fatura.loja, roles=['dono'], tipo='subscricao_fatura',
                    titulo=f'Nova fatura da subscrição — €{fatura.valor}' if nova else f'Fatura por pagar — €{fatura.valor}',
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
