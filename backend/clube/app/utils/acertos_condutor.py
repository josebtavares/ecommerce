"""
Acerto do dinheiro dos condutores.

Numa entrega paga em dinheiro, o condutor cobra ao cliente e fica com o dinheiro (Entrega.valor_recebido, gravado
quando marca "entregue"). Quando o entrega à loja, o dono/gestor (gerir_pagamentos) regista um acerto: escolhe as
entregas (por omissão todas), o total é a soma, e o condutor é avisado. O condutor vê sempre quanto tem consigo.

- Um acerto não se apaga: anular (com motivo) deixa o registo e as entregas voltam a ficar por acertar.
- Fica no registo das transacções (tipo 'acerto').
- Conta só o que foi cobrado a partir desta funcionalidade (as entregas antigas não têm valor_recebido).
"""
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Min, Sum
from django.utils import timezone

from .dinheiro import formatar as dinheiro

MOTIVO_MIN = 5


def _tempo_real(encomenda_id):
    """As entregas mudaram por .update() (sem sinais): avisa já pelo WebSocket quem tem a página aberta — o condutor
    e a loja (cartões 'por entregar / entregue à loja', separador Dinheiro). Um aviso chega: a página recarrega a
    lista toda (utils/tempoRealEncomendas.js)."""
    from .tempo_real_encomendas import emitir
    emitir(encomenda_id)


def nome_condutor(condutor):
    u = condutor.utilizador.user      # o mesmo nome que a lista das entregas mostra (EntregaSerializer)
    return (u.get_full_name() or u.username)[:150]


def por_acertar(loja, condutor=None):
    """Entregas em que o condutor cobrou dinheiro e ainda não o entregou à loja."""
    from ..models import Entrega
    qs = Entrega.objects.filter(encomenda__loja=loja, condutor__loja=loja, status='entregue',
                                valor_recebido__gt=0, acerto__isnull=True)
    if condutor is not None:
        qs = qs.filter(condutor=condutor)
    return qs


def resumo(loja):
    """Por condutor: quanto tem por entregar, em quantas entregas, desde quando."""
    from ..models import Condutor
    linhas = {r['condutor']: r for r in por_acertar(loja).values('condutor').annotate(
        total=Sum('valor_recebido'), n=Count('id'), desde=Min('data_entrega'))}
    saida = []
    for c in Condutor.objects.filter(loja=loja).select_related('utilizador__user'):
        r = linhas.get(c.id)
        if not r and not c.ativo:
            continue        # removido e sem nada por acertar: não aparece
        saida.append({'condutor_id': c.id, 'nome': nome_condutor(c), 'ativo': c.ativo,
                      'por_acertar': str(r['total'] if r else Decimal('0.00')), 'n': r['n'] if r else 0,
                      'desde': r['desde'] if r else None})
    saida.sort(key=lambda x: (-Decimal(x['por_acertar']), x['nome'].lower()))
    return saida


def entrega_dados(e):
    enc = e.encomenda
    comprador = getattr(enc, 'comprador', None)
    return {'entrega_id': e.id, 'encomenda_id': enc.id, 'valor': str(e.valor_recebido),
            'data_entrega': e.data_entrega,
            'cliente': (getattr(comprador, 'nome', '') or '') if comprador else '',
            'morada': enc.morada_entrega or ''}


def lista_por_acertar(loja, condutor):
    qs = por_acertar(loja, condutor).select_related('encomenda__comprador').order_by('data_entrega', 'id')
    return [entrega_dados(e) for e in qs]


def acerto_dados(a):
    return {'id': a.id, 'condutor_id': a.condutor_id, 'condutor_nome': a.condutor_nome, 'valor': str(a.valor),
            'n_entregas': a.n_entregas, 'encomendas': a.encomendas, 'nota': a.nota, 'criado_em': a.criado_em,
            'recebido_por': (a.recebido_por.get_full_name() or a.recebido_por.username) if a.recebido_por else '',
            'anulado': a.anulado, 'anulado_em': a.anulado_em, 'motivo_anulacao': a.motivo_anulacao,
            'anulado_por': (a.anulado_por.get_full_name() or a.anulado_por.username) if a.anulado_por else ''}


def historico(loja, condutor=None, n=30):
    from ..models import AcertoCondutor
    qs = AcertoCondutor.objects.filter(loja=loja).select_related('recebido_por', 'anulado_por')
    if condutor is not None:
        qs = qs.filter(condutor=condutor)
    return [acerto_dados(a) for a in qs[:n]]


def receber(loja, condutor, entrega_ids, por, nota=''):
    """A loja recebeu o dinheiro destas entregas. Devolve (acerto, erro)."""
    from ..models import AcertoCondutor
    from . import registo
    from ..Views.notificacaoView import notificar
    try:
        ids = sorted({int(i) for i in entrega_ids})
    except (TypeError, ValueError):
        return None, 'Entregas inválidas.'
    if not ids:
        return None, 'Escolhe pelo menos uma entrega.'
    with transaction.atomic():
        entregas = list(por_acertar(loja, condutor).filter(id__in=ids).select_for_update())
        if len(entregas) != len(ids):
            return None, 'Algumas entregas já foram acertadas ou não são deste condutor. Atualiza a lista.'
        valor = sum((e.valor_recebido for e in entregas), Decimal('0.00'))
        encomendas = sorted(e.encomenda_id for e in entregas)
        a = AcertoCondutor.objects.create(
            loja=loja, condutor=condutor, condutor_nome=nome_condutor(condutor), valor=valor,
            n_entregas=len(entregas), encomendas=encomendas, nota=str(nota or '').strip()[:300],
            recebido_por=por)
        type(entregas[0]).objects.filter(id__in=ids).update(acerto=a)
        _tempo_real(encomendas[0])
        registo.registar('acerto', 'recebido', objeto_id=a.id, loja_id=loja.id, valor=valor, metodo='dinheiro',
                         estado_novo='recebido', dados={'condutor': a.condutor_nome, 'encomendas': encomendas})
        notificar(
            utilizador=condutor.utilizador, tipo='acerto_condutor',
            titulo=f'{loja.nome} recebeu {dinheiro(valor)} de ti',
            mensagem=f'Dinheiro de {len(entregas)} entrega{"s" if len(entregas) != 1 else ""} '
                     f'(encomendas {", ".join("#" + str(i) for i in encomendas[:8])}'
                     f'{"…" if len(encomendas) > 8 else ""}).',
            loja=loja, link=f'/loja/{loja.id}/backoffice/entregas',
        )
    return a, None


def anular(acerto, por, motivo):
    """Engano no acerto: fica registado como anulado e as entregas voltam a estar por acertar. Devolve erro|None."""
    from ..models import AcertoCondutor, Entrega
    from . import registo
    from ..Views.notificacaoView import notificar
    motivo = str(motivo or '').strip()
    if len(motivo) < MOTIVO_MIN:
        return 'Indica o motivo (pelo menos 5 letras).'
    with transaction.atomic():
        a = AcertoCondutor.objects.select_for_update().get(pk=acerto.pk)
        if a.anulado:
            return 'Este acerto já foi anulado.'
        a.anulado, a.anulado_em, a.anulado_por, a.motivo_anulacao = True, timezone.now(), por, motivo[:300]
        a.save(update_fields=['anulado', 'anulado_em', 'anulado_por', 'motivo_anulacao'])
        Entrega.objects.filter(acerto=a).update(acerto=None)
        if a.encomendas:
            _tempo_real(a.encomendas[0])
        registo.registar('acerto', 'anulado', objeto_id=a.id, loja_id=a.loja_id, valor=a.valor, metodo='dinheiro',
                         estado_anterior='recebido', estado_novo='anulado',
                         dados={'condutor': a.condutor_nome, 'encomendas': a.encomendas, 'motivo': a.motivo_anulacao})
        notificar(
            utilizador=a.condutor.utilizador, tipo='acerto_condutor',
            titulo=f'Acerto de {dinheiro(a.valor)} anulado',
            mensagem=f'{a.loja.nome} anulou o registo: {a.motivo_anulacao}. Esse dinheiro volta a contar como estando contigo.',
            loja=a.loja, link=f'/loja/{a.loja_id}/backoffice/entregas',
        )
    return None
