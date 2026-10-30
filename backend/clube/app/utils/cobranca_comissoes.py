"""
Cobrança mensal das comissões (models.CobrancaComissoes).

A SISP não tem pagamento dividido: o dinheiro das vendas vai direto para a loja (contrato vinti4 dela, ou dinheiro/
transferência) e a Bende não pode descontar a comissão no pagamento. Por isso cobra-se à parte, uma vez por mês:

• emitir (worker, a partir do dia 1): as comissões da loja ainda por cobrar, registadas até ao fim do mês anterior,
  menos os créditos de reembolsos por descontar. Abaixo de VALOR_MINIMO não se emite — passa para o mês seguinte.
  As comissões e os créditos ficam presos à cobrança (cobranca_id).
• pagar: online (a Bende é aqui a comerciante — pagamentos.servico, referência com-<id>) ou registado pelo admin
  (transferência, dinheiro, oferta). As comissões ficam liquidadas e os créditos descontados.
• anular (admin, com motivo): solta as comissões e os créditos — entram na cobrança seguinte.
• reembolso de uma encomenda cuja comissão já está numa cobrança → crédito para a seguinte (utils/devolucoes),
  nunca muda o valor de uma cobrança já emitida.
• avisos ao dono: ao emitir, 3 dias antes, no dia e no primeiro dia em atraso (aos admins também). Não suspende
  nada sozinho — o admin decide.
"""
import logging
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

log = logging.getLogger(__name__)

DIAS_PARA_PAGAR = 10
VALOR_MINIMO = Decimal('100')
METODOS_ADMIN = ('transferencia', 'dinheiro', 'oferta', 'outro')


class ErroCobranca(Exception):
    pass


def _hoje():
    from .subscricoes import hoje
    return hoje()


def _inicio_do_mes(d):
    """Primeiro instante do mês de `d` no fuso da plataforma (aware)."""
    from .horarios import fuso
    return datetime.combine(d.replace(day=1), time.min, tzinfo=fuso())


def _mes_anterior(d):
    return (d.replace(day=1) - timedelta(days=1)).replace(day=1)


def _q(v):
    return (v or Decimal('0')).quantize(Decimal('0.01'))


# ── emitir ───────────────────────────────────────────────────────

def desde():
    """Instante a partir do qual se cobram comissões (Admin → Definições) | None = cobrança desligada."""
    from ..models import ConfiguracaoPlataforma
    return ConfiguracaoPlataforma.atual().cobrar_comissoes_desde


def por_cobrar(loja, ate, inicio):
    """(comissões, créditos) ainda soltos: comissões registadas entre `inicio` (ligar a cobrança) e `ate` (aware)."""
    from ..models import Comissao, CreditoComissao
    com = Comissao.objects.filter(loja=loja, status='pendente', cobranca__isnull=True, data_criacao__gte=inicio,
                                  data_criacao__lt=ate)
    cred = CreditoComissao.objects.filter(loja=loja, estado='pendente', cobranca__isnull=True,
                                          comissao__data_criacao__gte=inicio)
    return com, cred


def emitir(loja, d=None):
    """A cobrança do mês anterior a `d` (hoje) → CobrancaComissoes | None (nada, abaixo do mínimo ou já emitida)."""
    from ..models import CobrancaComissoes, Loja
    from .registo import registar
    d = d or _hoje()
    mes = _mes_anterior(d)
    inicio = desde()
    if not inicio:
        return None
    with transaction.atomic():
        Loja.objects.select_for_update().filter(pk=loja.pk).first()
        if CobrancaComissoes.objects.filter(loja=loja, mes=mes).exclude(estado='anulada').exists():
            return None
        com, cred = por_cobrar(loja, _inicio_do_mes(d), inicio)
        total_com = _q(com.aggregate(t=Sum('valor_comissao'))['t'])
        total_cred = _q(cred.aggregate(t=Sum('valor'))['t'])
        valor = total_com - total_cred
        if valor < VALOR_MINIMO:
            return None
        c = CobrancaComissoes.objects.create(loja=loja, mes=mes, valor_comissoes=total_com, valor_creditos=total_cred,
                                             valor=valor, vencimento=d + timedelta(days=DIAS_PARA_PAGAR))
        n_com = com.update(cobranca=c)
        cred.update(cobranca=c)
        registar('comissao', 'cobranca_emitida', objeto_id=c.id, loja_id=loja.id, valor=valor, estado_novo='pendente',
                 dados={'mes': f'{mes:%Y-%m}', 'comissoes': f'{total_com:.2f}', 'creditos': f'{total_cred:.2f}',
                        'n_comissoes': n_com})
        _avisar_dono(loja, 'Comissões a pagar',
                     f'As comissões das tuas vendas até {mes:%m/%Y}: {_dinheiro(valor)}. Paga até '
                     f'{c.vencimento:%d/%m/%Y} em Backoffice → Subscrição.')
    return c


def emitir_todas(d=None):
    """Worker: emite as cobranças que faltam (idempotente — corre todos os dias, emite uma vez por mês)."""
    from ..models import Comissao, Loja
    d = d or _hoje()
    inicio = desde()
    if not inicio:
        return 0
    ids = (Comissao.objects.filter(status='pendente', cobranca__isnull=True, data_criacao__gte=inicio,
                                   data_criacao__lt=_inicio_do_mes(d))
           .values_list('loja_id', flat=True).distinct())
    n = 0
    for loja in Loja.objects.filter(id__in=list(ids)):
        try:
            n += bool(emitir(loja, d))
        except Exception:
            log.exception('cobrança de comissões: loja %s falhou', loja.id)
    return n


# ── pagar / anular ───────────────────────────────────────────────

def _bloquear(c):
    from ..models import CobrancaComissoes
    return CobrancaComissoes.objects.select_for_update().get(pk=c.pk)


def pagar(c, metodo, referencia='', notas='', por=None):
    from .registo import registar
    with transaction.atomic():
        c = _bloquear(c)
        if c.estado != 'pendente':
            raise ErroCobranca('Esta cobrança já não está por pagar.')
        agora = timezone.now()
        c.estado, c.paga_em, c.metodo = 'paga', agora, metodo
        c.referencia, c.notas, c.registada_por = referencia[:100], notas[:300], por
        c.save()
        for com in c.comissoes.select_for_update().filter(status='pendente'):     # save(): cada uma fica no registo
            com.status, com.data_liquidacao = 'liquidada', agora
            com.save(update_fields=['status', 'data_liquidacao'])
        c.creditos.filter(estado='pendente').update(estado='descontado', data_desconto=agora)
        registar('comissao', 'cobranca_paga', objeto_id=c.id, loja_id=c.loja_id, valor=c.valor, estado_anterior='pendente',
                 estado_novo='paga', metodo=metodo, referencia=c.referencia)
        _avisar_dono(c.loja, 'Comissões pagas', f'Recebemos {_dinheiro(c.valor)} das comissões até {c.mes:%m/%Y}. Obrigado!')
    return c


def anular(c, motivo, por=None):
    from .registo import registar
    motivo = ' '.join(str(motivo or '').split())[:300]
    if len(motivo) < 5:
        raise ErroCobranca('Escreve o motivo.')
    with transaction.atomic():
        c = _bloquear(c)
        if c.estado != 'pendente':
            raise ErroCobranca('Só se anula uma cobrança por pagar.')
        c.estado, c.notas, c.registada_por = 'anulada', motivo, por
        c.save(update_fields=['estado', 'notas', 'registada_por'])
        c.comissoes.update(cobranca=None)       # voltam a estar por cobrar (entram na próxima)
        c.creditos.update(cobranca=None)
        registar('comissao', 'cobranca_anulada', objeto_id=c.id, loja_id=c.loja_id, valor=c.valor,
                 estado_anterior='pendente', estado_novo='anulada', dados={'motivo': motivo})
    return c


# ── avisos (worker) ──────────────────────────────────────────────

def avisar(d=None):
    from ..models import CobrancaComissoes
    d = d or _hoje()
    n = 0
    for c in CobrancaComissoes.objects.filter(estado='pendente', vencimento__lte=d + timedelta(days=3)).select_related('loja'):
        chave = 'atraso' if d > c.vencimento else 'd0' if d == c.vencimento else 'd3'
        if chave in c.avisos:
            continue
        texto = {'d3': f'As comissões ({_dinheiro(c.valor)}) vencem a {c.vencimento:%d/%m/%Y}.',
                 'd0': f'As comissões ({_dinheiro(c.valor)}) vencem hoje.',
                 'atraso': f'As comissões ({_dinheiro(c.valor)}) estão em atraso desde {c.vencimento:%d/%m/%Y}.'}[chave]
        _avisar_dono(c.loja, 'Comissões a pagar', texto + ' Backoffice → Subscrição.')
        if chave == 'atraso':
            from ..Views.notificacaoView import notificar_admins
            notificar_admins(tipo='cobranca_comissoes', titulo='Comissões em atraso',
                             mensagem=f'{c.loja.nome}: {_dinheiro(c.valor)} desde {c.vencimento:%d/%m/%Y}.', loja=c.loja,
                             link='/admin/comissoes')
        CobrancaComissoes.objects.filter(pk=c.pk).update(avisos=[*c.avisos, chave])
        n += 1
    return n


# ── leitura ──────────────────────────────────────────────────────

def _dinheiro(v):
    from .dinheiro import formatar
    return formatar(v)


def _avisar_dono(loja, titulo, mensagem):
    try:
        from ..Views.notificacaoView import notificar_staff
        notificar_staff(loja=loja, roles=['dono'], tipo='cobranca_comissoes', titulo=titulo, mensagem=mensagem,
                        link=f'/loja/{loja.id}/backoffice/subscricao')
    except Exception:          # a cobrança já está gravada: o aviso não a pode estragar
        log.exception('cobrança de comissões: aviso ao dono falhou')


def payload(c, d=None):
    d = d or _hoje()
    return {
        'id': c.id, 'loja_id': c.loja_id, 'loja_nome': c.loja.nome, 'mes': c.mes.isoformat(),
        'valor_comissoes': f'{c.valor_comissoes:.2f}', 'valor_creditos': f'{c.valor_creditos:.2f}', 'valor': f'{c.valor:.2f}',
        'estado': c.estado, 'estado_nome': c.get_estado_display(), 'em_atraso': c.estado == 'pendente' and d > c.vencimento,
        'vencimento': c.vencimento.isoformat(), 'emitida_em': c.emitida_em.isoformat(),
        'paga_em': c.paga_em.isoformat() if c.paga_em else None, 'metodo': c.metodo,
        'metodo_nome': c.get_metodo_display() if c.metodo else '', 'referencia': c.referencia, 'notas': c.notas,
    }


def resumo_loja(loja):
    """Para o backoffice: cobranças + o que se está a acumular este mês (ainda não cobrado)."""
    from ..models import Comissao, CreditoComissao
    inicio = desde()
    if inicio:
        acumular = _q(Comissao.objects.filter(loja=loja, status='pendente', cobranca__isnull=True, data_criacao__gte=inicio)
                      .aggregate(t=Sum('valor_comissao'))['t'])
        creditos = _q(CreditoComissao.objects.filter(loja=loja, estado='pendente', cobranca__isnull=True,
                                                     comissao__data_criacao__gte=inicio).aggregate(t=Sum('valor'))['t'])
    else:
        acumular = creditos = Decimal('0')
    cobrancas = list(loja.cobrancas_comissoes.select_related('loja').exclude(estado='anulada')[:24])
    return {'cobrancas': [payload(c) for c in cobrancas],
            'a_acumular': f'{acumular:.2f}', 'creditos': f'{creditos:.2f}',
            'por_pagar': f'{sum((c.valor for c in cobrancas if c.estado == "pendente"), Decimal("0")):.2f}',
            'dias_para_pagar': DIAS_PARA_PAGAR, 'minimo': f'{VALOR_MINIMO:.2f}', 'ligada': bool(inicio)}
