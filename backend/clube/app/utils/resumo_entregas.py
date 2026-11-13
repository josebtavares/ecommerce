"""
Resumo do dia das entregas (separador Entregas, no topo).

Conta o que aconteceu no dia (hora de Cabo Verde) a partir de TentativaEntrega — gravada quando a entrega é
marcada entregue ou falhada (a Entrega em si é reatribuída e muda de condutor, a tentativa fica):
entregues, falhadas, dinheiro cobrado e quantas com prova. Para hoje junta ainda as que estão por fazer
(em curso e não agendadas para depois de hoje) e o dinheiro que cada condutor tem por entregar à loja.

A loja vê todos os condutores; o condutor só o seu.
"""
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.utils import timezone

DIAS_MAX = 366


def _limites(dia):
    tz = timezone.get_current_timezone()
    ini = timezone.make_aware(datetime.combine(dia, time.min), tz)
    return ini, ini + timedelta(days=1)


def _linha(nome, condutor_id):
    return {'condutor_id': condutor_id, 'nome': nome, 'entregues': 0, 'falhadas': 0, 'cobrado': Decimal('0.00'),
            'com_prova': 0, 'por_fazer': 0, 'por_acertar': Decimal('0.00')}


def do_dia(loja, dia, condutor=None):
    from ..models import Condutor, Entrega, TentativaEntrega
    from .acertos_condutor import nome_condutor, por_acertar
    from .encomendas import ENTREGA_EM_CURSO

    hoje = timezone.localdate()
    ini, fim = _limites(dia)
    linhas = {}

    def linha(cid):
        if cid not in linhas:
            linhas[cid] = _linha('', cid)
        return linhas[cid]

    t = TentativaEntrega.objects.filter(loja=loja, criado_em__gte=ini, criado_em__lt=fim)
    if condutor:
        t = t.filter(condutor=condutor)
    for r in t.values('condutor_id').annotate(
            ent=Count('id', filter=Q(resultado='entregue')), fal=Count('id', filter=Q(resultado='falhou')),
            cob=Sum('valor_recebido', filter=Q(resultado='entregue')),
            prova=Count('id', filter=Q(resultado='entregue') & (~Q(entrega__prova_foto='') |
                                                                 ~Q(entrega__prova_assinatura='') |
                                                                 ~Q(entrega__recebido_por_nome=''))),
    ):
        x = linha(r['condutor_id'])
        x['entregues'], x['falhadas'], x['com_prova'] = r['ent'], r['fal'], r['prova']
        x['cobrado'] = r['cob'] or Decimal('0.00')

    if dia == hoje:
        em_curso = Entrega.objects.filter(encomenda__loja=loja, tipo='condutor', status__in=ENTREGA_EM_CURSO).filter(
            Q(encomenda__agendada_para__isnull=True) | Q(encomenda__agendada_para__lt=fim))
        if condutor:
            em_curso = em_curso.filter(condutor=condutor)
        for r in em_curso.values('condutor_id').annotate(n=Count('id')):
            linha(r['condutor_id'])['por_fazer'] = r['n']
        for r in por_acertar(loja, condutor).values('condutor_id').annotate(v=Sum('valor_recebido')):
            linha(r['condutor_id'])['por_acertar'] = r['v'] or Decimal('0.00')

    nomes = {c.id: nome_condutor(c) for c in Condutor.objects.filter(id__in=[k for k in linhas if k])
             .select_related('utilizador__user')}
    for cid, x in linhas.items():
        x['nome'] = nomes.get(cid, '') if cid else 'Sem condutor'

    ordem = sorted(linhas.values(), key=lambda x: (x['condutor_id'] is None, x['nome'].lower()))
    total = _linha('Total', None)
    for x in ordem:
        for k in ('entregues', 'falhadas', 'cobrado', 'com_prova', 'por_fazer', 'por_acertar'):
            total[k] += x[k]
    for x in ordem + [total]:
        x['cobrado'], x['por_acertar'] = str(x['cobrado']), str(x['por_acertar'])
    return {'data': dia.isoformat(), 'hoje': dia == hoje, 'total': total,
            'condutores': [] if condutor else ordem}
