"""
Admin: registo das transações (utils/registo.py) e dados bancários das lojas.

GET /app/admin/registo/?tipo=&loja=&encomenda=&evento=&de=AAAA-MM-DD&ate=AAAA-MM-DD&offset=&limit=
GET /app/admin/registo/exportar/   (mesmos filtros) → CSV
GET /app/admin/registo/verificar/  → { total, ok, primeiro_erro }
GET /app/admin/lojas/<id>/banco/   → dados bancários completos (fica no registo quem viu)
"""
import csv
import re
from datetime import datetime, time, timedelta

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import DadosBancarios, Loja, RegistoTransacao
from ..utils import banco
from ..utils.horarios import fuso
from ..utils.registo import registar, selar, verificar_cadeia
from .adminView import _exige_admin

MAX_EXPORTAR = 50000


def _data(texto):
    try:
        return datetime.strptime(texto, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


def _filtrar(request):
    qs = RegistoTransacao.objects.all()
    g = request.GET
    if g.get('tipo') in dict(RegistoTransacao.TIPOS):
        qs = qs.filter(tipo=g['tipo'])
    for campo, chave in (('loja_id', 'loja'), ('encomenda_id', 'encomenda'), ('objeto_id', 'objeto')):
        if (g.get(chave) or '').isdigit() and len(g[chave]) <= 18:      # cabe num bigint
            qs = qs.filter(**{campo: int(g[chave])})
    if g.get('evento'):
        qs = qs.filter(evento=g['evento'][:40])
    tz = fuso()
    de, ate = _data(g.get('de')), _data(g.get('ate'))
    if de:
        qs = qs.filter(criado_em__gte=timezone.make_aware(datetime.combine(de, time.min), tz))
    if ate:
        qs = qs.filter(criado_em__lt=timezone.make_aware(datetime.combine(ate + timedelta(days=1), time.min), tz))
    return qs


def _linhas(registos):
    ids = {r.ator_id for r in registos if r.ator_id}
    nomes = dict(User.objects.filter(id__in=ids).values_list('id', 'username'))
    tz = fuso()
    for r in registos:
        yield {
            'id': r.id,
            'quando': r.criado_em.astimezone(tz).strftime('%d/%m/%Y %H:%M:%S'),
            'criado_em': r.criado_em.isoformat(),
            'tipo': r.tipo, 'tipo_label': r.get_tipo_display(), 'evento': r.evento,
            'objeto_id': r.objeto_id, 'loja_id': r.loja_id, 'pos_id': r.pos_id, 'encomenda_id': r.encomenda_id,
            'valor': None if r.valor is None else f'{r.valor:.2f}',
            'estado_anterior': r.estado_anterior, 'estado_novo': r.estado_novo,
            'metodo': r.metodo, 'referencia': r.referencia,
            'ator': nomes.get(r.ator_id, f'#{r.ator_id}') if r.ator_id else 'sistema',
            'ip': r.ip, 'pedido_id': r.pedido_id, 'dados': r.dados,
            'seq': r.seq, 'hash_conteudo': r.hash_conteudo, 'hash_anterior': r.hash_anterior, 'hash': r.hash or '',
        }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_registo(request):
    erro = _exige_admin(request, 'ver_registo_transacoes')
    if erro: return erro
    selar()                 # o que ficou por selar (ex.: o worker caiu a meio) aparece já com o elo
    qs = _filtrar(request)
    try:
        offset = max(0, int(request.GET.get('offset', 0)))
        limit = min(100, max(1, int(request.GET.get('limit', 50))))
    except ValueError:
        offset, limit = 0, 50
    total = qs.count()
    pagina = list(qs[offset:offset + limit])
    return Response({
        'count': total,
        'next_offset': offset + limit if offset + limit < total else None,
        'results': list(_linhas(pagina)),
        'tipos': [{'valor': v, 'label': l} for v, l in RegistoTransacao.TIPOS],
    })


def _celula(v):
    """Texto que o Excel leria como fórmula (=, +, -, @…) vai com um apóstrofo à frente (CSV injection)."""
    t = '' if v is None else str(v)
    if re.fullmatch(r'-?\d+(\.\d+)?', t):
        return t
    return "'" + t if t[:1] in ('=', '+', '-', '@', '\t', '\r') else t


def _escrever(w, cab, registos):
    for l in _linhas(registos):
        l['dados'] = '; '.join(f'{k}={v}' for k, v in l['dados'].items())
        w.writerow([_celula(l[c]) for c in cab])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_registo_exportar(request):
    erro = _exige_admin(request, 'ver_registo_transacoes')
    if erro: return erro
    selar()
    qs = _filtrar(request).order_by('id')[:MAX_EXPORTAR]
    resp = HttpResponse(content_type='text/csv; charset=utf-8')
    resp['Content-Disposition'] = f'attachment; filename="registo-transacoes-{timezone.localdate():%Y%m%d}.csv"'
    resp.write('﻿')      # BOM: o Excel abre os acentos certos
    w = csv.writer(resp, delimiter=';')
    cab = ['id', 'criado_em', 'quando', 'tipo', 'evento', 'objeto_id', 'loja_id', 'pos_id', 'encomenda_id', 'valor',
           'estado_anterior', 'estado_novo', 'metodo', 'referencia', 'ator', 'ip', 'pedido_id', 'dados',
           'seq', 'hash_conteudo', 'hash_anterior', 'hash']
    w.writerow(cab)
    lote = []
    for r in qs.iterator(chunk_size=1000):
        lote.append(r)
        if len(lote) == 1000:
            _escrever(w, cab, lote)
            lote = []
    _escrever(w, cab, lote)
    return resp


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_registo_verificar(request):
    erro = _exige_admin(request, 'ver_registo_transacoes')
    if erro: return erro
    return Response(verificar_cadeia())


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_loja_banco(request, loja_id):
    erro = _exige_admin(request, 'gerir_pagamentos')
    if erro: return erro
    loja = get_object_or_404(Loja, id=loja_id)
    d = DadosBancarios.objects.filter(loja=loja).first()
    if d:
        registar('banco', 'consultados_admin', objeto_id=loja.id, loja_id=loja.id,
                 dados={'conta': banco.mascarado(d.nib)})
    return Response({'dados': banco.payload(d)})
