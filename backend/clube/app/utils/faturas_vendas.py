"""
Vendas que a loja/POS fatura (emite a fatura no e-Fatura e regista-a no Bende) — três origens:
  'loja'       Encomenda (loja online)        E-<id>   data da venda: data_criacao
  'marcacoes'  Marcacao (serviços da loja)    M-<id>   data: inicio (o dia do serviço)
  'pos'        ContaMesa (POS)                V-<id>   data: fechada_em
Faturável: encomenda paga/em curso; marcação que rendeu dinheiro (concluída, ou falta/cancelada paga e não
devolvida — a mesma receita dos relatórios dos serviços); conta do POS fechada com total > 0.
Uma venda que teve fatura fica no arquivo mesmo que deixe de ser faturável (ex.: encomenda cancelada depois).
As contas de um POS ligado contam na loja (aba da loja no admin); as de um POS sem loja, no POS.
"""
import re
from decimal import Decimal, InvalidOperation

from django.db.models import Case, Count, DecimalField, F, Q, Sum, Value, When
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from . import fiscal

ORIGENS = ('loja', 'marcacoes', 'pos')
NOMES = {'loja': 'Loja online', 'marcacoes': 'Marcações', 'pos': 'POS'}
ZERO = Decimal('0')
CAMPO_DATA = {'loja': 'data_criacao', 'marcacoes': 'inicio', 'pos': 'fechada_em'}
CAMPO_VALOR = {'loja': 'valor_total', 'marcacoes': 'receita', 'pos': 'total'}
HISTORICO = {'loja': ('encomenda', 'encomenda_id'), 'marcacoes': ('marcacao', 'marcacao_id'), 'pos': ('venda_pos', 'conta_id')}
CONFLITO = 'A fatura foi alterada entretanto (outro pedido). Recarrega a página e tenta de novo.'


def _modelo(origem):
    if origem == 'loja':
        from ..models import Encomenda
        return Encomenda
    if origem == 'marcacoes':
        from ..servicos.models import Marcacao
        return Marcacao
    from ..pos.models import ContaMesa
    return ContaMesa


def base(origem):
    """Queryset da origem; as marcações levam o preço efetivo e a receita (o valor da fatura)."""
    qs = _modelo(origem).objects.all()
    if origem == 'marcacoes':
        dec = DecimalField(max_digits=12, decimal_places=2)
        qs = qs.annotate(preco_ef=Coalesce('preco_final', 'preco_indicado')).annotate(receita=Case(
            # concluída: o preço (o que se devolveu foi só o pago a mais — o cliente pagou o preço)
            When(estado='concluida', then=F('preco_ef')),
            When(estado__in=('falta', 'cancelada'), pago=True, then=F('valor_pago') - F('valor_reembolsado')),
            default=Value(ZERO), output_field=dec))
    return qs


def q_faturavel(origem):
    if origem == 'loja':
        return Q(status__in=fiscal.ESTADOS_FATURAVEIS)
    if origem == 'marcacoes':
        return Q(receita__gt=0)
    return Q(status='fechada', total__gt=0)


def q_por_faturar(origem):
    """Faturável e sem fatura em vigor (uma venda que deixou de ser faturável não fica por faturar)."""
    return q_faturavel(origem) & Q(fatura_registada_em__isnull=True)


def com_fatura(origem):
    tipo, campo = HISTORICO[origem]
    from ..models import HistoricoFatura
    return HistoricoFatura.objects.filter(tipo=tipo, **{f'{campo}__isnull': False}).values(campo)


def vendas(origem, loja=None, pos=None, de=None, ate=None):
    """
    Vendas faturáveis (e as que tiveram fatura) de uma loja — loja online, marcações ou os POS ligados — ou de um POS.
    Sem loja nem POS: de todos. de/ate: dias (fuso da plataforma).
    """
    qs = base(origem).filter(q_faturavel(origem) | Q(id__in=com_fatura(origem)))
    if origem == 'pos':
        if pos is not None:
            qs = qs.filter(pos=pos)
        elif loja is not None:
            qs = qs.filter(pos__loja_vinculada=loja)
    elif loja is not None:
        qs = qs.filter(loja=loja)
    campo = CAMPO_DATA[origem]
    if de:
        qs = qs.filter(**{f'{campo}__date__gte': de})
    if ate:
        qs = qs.filter(**{f'{campo}__date__lte': ate})
    return qs


def valor(origem, qs):
    """Soma do que os clientes pagaram (encomendas: sem os artigos esgotados abatidos antes de pagar)."""
    if origem == 'loja':
        from ..models import Reembolso
        total = qs.aggregate(t=Sum('valor_total'))['t'] or ZERO
        abatido = (Reembolso.objects.filter(encomenda__in=qs.values('id'), estado='reembolsado', metodo='abatido')
                   .aggregate(t=Sum('valor_aprovado'))['t'] or ZERO)
        return total - abatido
    return qs.aggregate(t=Sum(CAMPO_VALOR[origem]))['t'] or ZERO


def valor_de(origem, obj):
    if origem == 'loja':
        return obj.valor_devido
    if origem == 'marcacoes':
        return obj.receita if hasattr(obj, 'receita') else base('marcacoes').get(pk=obj.pk).receita
    return obj.total


def faturavel(origem, obj):
    return base(origem).filter(q_faturavel(origem), pk=obj.pk).exists()


def contagens(origem, chave, **filtro):
    """{valor da chave: {vendas, faturadas, por_faturar}} — ex.: contagens('pos', 'pos__loja_vinculada_id')."""
    qs = vendas(origem, de=filtro.pop('de', None), ate=filtro.pop('ate', None)).filter(**filtro)
    out = {}
    for r in (qs.order_by().values(chave)
              .annotate(n=Count('id'), fat=Count('id', filter=Q(fatura_registada_em__isnull=False)),
                        pf=Count('id', filter=q_por_faturar(origem)))):
        out[r[chave]] = {'vendas': r['n'], 'faturadas': r['fat'], 'por_faturar': r['pf']}
    return out


def somar(*dicts):
    """Soma contagens de várias origens: {chave: {vendas, faturadas, por_faturar}}."""
    out = {}
    for d in dicts:
        for k, v in d.items():
            t = out.setdefault(k, {'vendas': 0, 'faturadas': 0, 'por_faturar': 0})
            for c in t:
                t[c] += v[c]
    return out


def filtrar(origem, qs, q=''):
    """?q= nº da venda (E-/M-/V-/#), nº de fatura (também anulada), cliente."""
    q = (q or '').strip().lstrip('#')
    if not q:
        return qs
    tipo, campo = HISTORICO[origem]
    from ..models import HistoricoFatura
    cond = Q(fatura_numero__icontains=q) | Q(id__in=HistoricoFatura.objects.filter(tipo=tipo, numero__icontains=q).values(campo))
    if origem == 'loja':
        cond |= (Q(comprador__user__email__icontains=q) | Q(comprador__user__username__icontains=q) |
                 Q(comprador__user__first_name__icontains=q) | Q(comprador__user__last_name__icontains=q))
        prefixo = 'e'
    elif origem == 'marcacoes':
        cond |= (Q(cliente_nome__icontains=q) | Q(cliente_telefone__icontains=q) | Q(servico_nome__icontains=q) |
                 Q(cliente__user__email__icontains=q) | Q(cliente__user__first_name__icontains=q) |
                 Q(cliente__user__last_name__icontains=q))
        prefixo = 'm'
    else:
        cond |= Q(nif_cliente__icontains=q) | Q(atendente_nome__icontains=q) | Q(mesa__numero__icontains=q)
        prefixo = 'v'
    num = re.sub(rf'^[{prefixo}{prefixo.upper()}]-', '', q)
    if num.isdigit():
        cond |= Q(id=int(num))
    return qs.filter(cond)


def filtrar_valor(origem, qs, minimo, maximo):
    """Devolve (qs, erro)."""
    for v, op in ((minimo, 'gte'), (maximo, 'lte')):
        if not v:
            continue
        try:
            qs = qs.filter(**{f'{CAMPO_VALOR[origem]}__{op}': Decimal(str(v).replace(',', '.'))})
        except InvalidOperation:
            return None, 'Valor inválido.'
    return qs, None


def com_relacoes(origem, qs):
    if origem == 'loja':
        return qs.select_related('comprador__user', 'pagamento', 'loja')
    if origem == 'marcacoes':
        return qs.select_related('cliente__user', 'loja')
    return qs.select_related('mesa', 'pos')


def referencia(origem, obj):
    return {'loja': 'E', 'marcacoes': 'M', 'pos': 'V'}[origem] + f'-{obj.id}'


def cliente(origem, obj):
    """{nome, email} de quem comprou (no POS: o NIF que o cliente pediu na fatura, se pediu)."""
    if origem == 'loja':
        u = obj.comprador.user
        return {'nome': u.get_full_name() or u.username, 'email': u.email}
    if origem == 'marcacoes':
        if obj.cliente_id:
            u = obj.cliente.user
            return {'nome': u.get_full_name() or u.username or obj.cliente_nome, 'email': u.email}
        return {'nome': obj.cliente_nome or '—', 'email': obj.cliente_telefone}
    return {'nome': f'NIF {obj.nif_cliente}' if obj.nif_cliente else 'Consumidor final', 'email': ''}


def titulo(origem, obj):
    if origem == 'loja':
        return f'Encomenda #{obj.id}'
    if origem == 'marcacoes':
        return f'Marcação #{obj.id} · {obj.servico_nome}'
    return f'Conta #{obj.id} · {obj.mesa.numero}'


def estado_nome(origem, obj):
    if origem == 'loja':
        return obj.get_status_display()
    if origem == 'marcacoes':
        return obj.get_estado_display()
    return f'Paga · {obj.get_metodo_pagamento_display() or "—"}' if obj.status == 'fechada' else obj.get_status_display()


def linha(origem, obj, request=None, anuladas=0):
    """Uma venda nas listas do admin (e na pesquisa)."""
    d = {'id': obj.id, 'origem': origem, 'referencia': referencia(origem, obj), 'titulo': titulo(origem, obj),
         'data': getattr(obj, CAMPO_DATA[origem]), 'cliente': cliente(origem, obj),
         'valor': str(valor_de(origem, obj)), 'status': obj.estado if origem == 'marcacoes' else obj.status,
         'status_nome': estado_nome(origem, obj), 'comprovativo': False,
         'fatura': fiscal.fatura_resumo(obj, request), 'anuladas': anuladas}
    if origem == 'loja':
        pag = getattr(obj, 'pagamento', None)
        d['comprovativo'] = bool(pag and pag.status in ('aprovado', 'reembolsado', 'reembolsado_parcial'))
    if origem == 'pos':
        d['pos'] = {'id': obj.pos_id, 'nome': obj.pos.nome}
    return d


def anuladas_por(origem, ids):
    tipo, campo = HISTORICO[origem]
    from ..models import HistoricoFatura
    n = {}
    for v in HistoricoFatura.objects.filter(tipo=tipo, anulada_em__isnull=False, **{f'{campo}__in': ids}).values_list(campo, flat=True):
        n[v] = n.get(v, 0) + 1
    return n


# ── Registar / substituir / anular (loja nas marcações, POS nas contas) ──

def pedido(request, obj, origem, user):
    """
    POST numero + pdf (+ motivo ao substituir) regista; DELETE {motivo} anula.
    Devolve (evento, numero_anulado, erro): evento 'registada' | 'substituida' | 'anulada' | None; erro é uma Response.
    """
    motivo = ''
    if request.method == 'DELETE' or obj.fatura_registada_em:
        motivo, msg = fiscal.validar_motivo(request.data.get('motivo'))
        if msg:
            return None, '', Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)
    try:
        if request.method == 'DELETE':
            if not obj.fatura_registada_em:
                return None, '', None
            numero = obj.fatura_numero
            fiscal.anular_fatura(obj, user, motivo)
            return 'anulada', numero, None
        if not faturavel(origem, obj):
            msg = ('Só se regista a fatura de uma marcação que rendeu dinheiro (concluída, ou falta paga).'
                   if origem == 'marcacoes' else 'Só se regista a fatura de uma conta fechada (paga).')
            return None, '', Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)
        pdf = request.FILES.get('pdf')
        numero, msg = fiscal.validar_fatura(request.data.get('numero'), pdf)
        if msg:
            return None, '', Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)
        evento = 'substituida' if obj.fatura_registada_em else 'registada'
        fiscal.registar_fatura(obj, numero, pdf, user, motivo)
        return evento, '', None
    except fiscal.FaturaAlterada:
        return None, '', Response({'detail': CONFLITO}, status=status.HTTP_409_CONFLICT)


def quando(dt, fmt='%d/%m/%Y %H:%M'):
    return f'{timezone.localtime(dt):{fmt}}' if dt else ''
