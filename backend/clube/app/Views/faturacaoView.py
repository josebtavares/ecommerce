"""
Faturação — documentos internos (comprovativos, extrato de comissões) e as faturas registadas.

Cliente/loja:
  GET  /app/encomenda/<id>/comprovativo/                    comprovativo da encomenda paga (PDF)
  GET  /app/subscricao/faturas/<id>/comprovativo/           comprovativo da mensalidade paga (PDF)
  GET  /app/loja/<id>/comissoes/meses/                      comissões por mês + fatura do Bende
  GET  /app/loja/<id>/comissoes/<AAAA-MM>/extrato/          extrato do mês (PDF)
Admin (gerir_faturacao):
  GET  /app/admin/faturacao/vendedores/?de=&ate=&q=         dados fiscais + vendas faturadas/por faturar
  GET  /app/admin/faturacao/vendas.csv?loja=&de=&ate=       vendas de uma loja com as faturas (para a DNRE)
  GET  /app/admin/faturacao/bende/?mes=AAAA-MM              o que o Bende tem de faturar no mês
  POST/DELETE /app/admin/faturacao/subscricoes/<id>/fatura/            fatura do Bende de uma mensalidade
  POST/DELETE /app/admin/faturacao/comissoes/<loja>/<AAAA-MM>/fatura/   fatura do Bende das comissões do mês
  GET  /app/admin/faturacao/comissoes/<loja>/<AAAA-MM>/extrato/
"""
import csv
from datetime import date, datetime, timedelta

from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Comissao, Encomenda, FaturaComissoes, FaturaSubscricao, Loja, UtilizadorLoja
from ..pos.models import ConfiguracaoPOS
from ..utils import documentos, fiscal
from ..utils.emails_fiscais import enviar_fatura_comissoes, enviar_fatura_subscricao
from ..utils.subscricoes import fatura_payload, nome_alvo
from .adminView import _exige_admin


def _pdf(conteudo, nome):
    r = HttpResponse(conteudo, content_type='application/pdf')
    r['Content-Disposition'] = f'attachment; filename="{nome}"'
    return r


def _mes(texto):
    """'2026-10' → date(2026, 10, 1); None se inválido."""
    try:
        return datetime.strptime(texto or '', '%Y-%m').date()
    except ValueError:
        return None


def _periodo(request):
    """?de=AAAA-MM-DD&ate=AAAA-MM-DD (inclusive); por defeito o mês corrente."""
    hoje = timezone.localdate()
    try:
        de = date.fromisoformat(request.GET['de']) if request.GET.get('de') else hoje.replace(day=1)
        ate = date.fromisoformat(request.GET['ate']) if request.GET.get('ate') else hoje
    except ValueError:
        return None, None
    return de, ate


def _membro(request, loja):
    try:
        return UtilizadorLoja.objects.get(loja=loja, utilizador=request.user.utilizador, ativo=True)
    except Exception:
        return None


# ── Comprovativos ──────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def encomenda_comprovativo(request, id):
    enc = get_object_or_404(Encomenda.objects.select_related('loja', 'comprador__user'), id=id)
    eh_comprador = getattr(request.user, 'utilizador', None) == enc.comprador
    if not eh_comprador and not _membro(request, enc.loja) and _exige_admin(request, 'gerir_faturacao'):
        return Response({'detail': 'Sem permissão.'}, status=status.HTTP_403_FORBIDDEN)
    pag = getattr(enc, 'pagamento', None)
    if not pag or pag.status not in ('aprovado', 'reembolsado', 'reembolsado_parcial'):
        return Response({'detail': 'A encomenda ainda não está paga.'}, status=status.HTTP_400_BAD_REQUEST)
    return _pdf(documentos.pdf_comprovativo_encomenda(enc), documentos.nome_comprovativo_encomenda(enc))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def subscricao_comprovativo(request, fatura_id):
    f = get_object_or_404(FaturaSubscricao.objects.select_related('loja', 'pos', 'plano'), id=fatura_id)
    pode = (not _exige_admin(request, 'gerir_subscricoes')) or (not _exige_admin(request, 'gerir_faturacao'))
    if not pode and f.loja_id:
        m = _membro(request, f.loja)
        pode = bool(m and m.pode('ver_subscricao'))
    if not pode and f.pos_id:
        pode = f.pos.dono_id == getattr(getattr(request.user, 'utilizador', None), 'id', None)
    if not pode:
        return Response({'detail': 'Sem permissão.'}, status=status.HTTP_403_FORBIDDEN)
    if f.estado != 'paga':
        return Response({'detail': 'A mensalidade ainda não está paga.'}, status=status.HTTP_400_BAD_REQUEST)
    return _pdf(documentos.pdf_comprovativo_subscricao(f), documentos.nome_comprovativo_subscricao(f))


# ── Comissões (loja) ───────────────────────────────────────────

def _comissoes_por_mes(loja):
    from django.db.models.functions import TruncMonth
    meses = (Comissao.objects.filter(loja=loja).annotate(m=TruncMonth('data_criacao'))
             .values('m').annotate(total=Sum('valor_comissao'), n=Count('id')).order_by('-m'))
    faturas = {fc.mes: fc for fc in FaturaComissoes.objects.filter(loja=loja)}
    out = []
    for r in meses:
        mes = timezone.localtime(r['m']).date().replace(day=1) if hasattr(r['m'], 'tzinfo') else r['m'].replace(day=1)
        out.append({'mes': f'{mes:%Y-%m}', 'total': str(r['total']), 'comissoes': r['n'],
                    'fatura': fiscal.fatura_resumo(faturas.get(mes))})
    return out


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loja_comissoes_meses(request, loja_id):
    loja = get_object_or_404(Loja, id=loja_id)
    m = _membro(request, loja)
    if not m or not m.pode('ver_subscricao'):
        return Response({'detail': 'Sem permissão.'}, status=status.HTTP_403_FORBIDDEN)
    return Response({'meses': _comissoes_por_mes(loja)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loja_comissoes_extrato(request, loja_id, mes):
    loja = get_object_or_404(Loja, id=loja_id)
    m = _membro(request, loja)
    if (not m or not m.pode('ver_subscricao')) and _exige_admin(request, 'gerir_faturacao'):
        return Response({'detail': 'Sem permissão.'}, status=status.HTTP_403_FORBIDDEN)
    d = _mes(mes)
    if not d:
        return Response({'detail': 'Mês inválido (AAAA-MM).'}, status=status.HTTP_400_BAD_REQUEST)
    return _pdf(documentos.pdf_extrato_comissoes(loja, d), documentos.nome_extrato_comissoes(loja, d))


# ── Admin ──────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_vendedores(request):
    erro = _exige_admin(request, 'gerir_faturacao')
    if erro:
        return erro
    de, ate = _periodo(request)
    if not de:
        return Response({'detail': 'Datas inválidas.'}, status=status.HTTP_400_BAD_REQUEST)
    q = (request.GET.get('q') or '').strip()
    vendas = Q(encomendas__status__in=fiscal.ESTADOS_FATURAVEIS,
               encomendas__data_criacao__date__gte=de, encomendas__data_criacao__date__lte=ate)
    lojas = (Loja.objects.exclude(estado='pendente').select_related('dono__user')
             .annotate(vendas=Count('encomendas', filter=vendas),
                       faturadas=Count('encomendas', filter=vendas & Q(encomendas__fatura_registada_em__isnull=False)))
             .order_by('nome'))
    posq = ConfiguracaoPOS.objects.filter(ativo=True).select_related('dono__user').order_by('nome')
    if q:
        lojas = lojas.filter(Q(nome__icontains=q) | Q(nif__icontains=q))
        posq = posq.filter(Q(nome__icontains=q) | Q(nif__icontains=q) | Q(codigo_pos__icontains=q))

    def base(obj, tipo, nome):
        return {'tipo': tipo, 'id': obj.id, 'nome': nome, 'dono': obj.dono.user.get_full_name() or obj.dono.user.username,
                'dono_email': obj.dono.user.email, **fiscal.dados_fiscais_payload(obj)}
    itens = [{**base(l, 'loja', l.nome), 'vendas': l.vendas, 'faturadas': l.faturadas,
              'por_faturar': l.vendas - l.faturadas} for l in lojas[:500]]
    itens += [{**base(p, 'pos', nome_alvo(p)), 'vendas': None, 'faturadas': None, 'por_faturar': None} for p in posq[:500]]
    return Response({'de': de, 'ate': ate, 'itens': itens})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_vendas_csv(request):
    erro = _exige_admin(request, 'gerir_faturacao')
    if erro:
        return erro
    de, ate = _periodo(request)
    loja = get_object_or_404(Loja, id=request.GET.get('loja') or 0)
    if not de:
        return Response({'detail': 'Datas inválidas.'}, status=status.HTTP_400_BAD_REQUEST)
    qs = (Encomenda.objects.filter(loja=loja, status__in=fiscal.ESTADOS_FATURAVEIS,
                                   data_criacao__date__gte=de, data_criacao__date__lte=ate)
          .select_related('comprador__user').order_by('data_criacao'))
    r = HttpResponse(content_type='text/csv; charset=utf-8')
    r['Content-Disposition'] = f'attachment; filename="vendas-{loja.id}-{de}-{ate}.csv"'
    r.write('﻿')     # Excel abre com acentos
    w = csv.writer(r, delimiter=';')
    w.writerow([f'Loja: {loja.nome}', f'NIF: {loja.nif or "—"}', f'Regime: {loja.get_regime_fiscal_display() or "—"}',
                f'Declaração aceite: {timezone.localtime(loja.dados_fiscais_aceites_em):%d/%m/%Y %H:%M}' if loja.dados_fiscais_aceites_em else 'Declaração: por aceitar'])
    w.writerow(['Encomenda', 'Data', 'Cliente', 'Valor (CVE)', 'Estado', 'Fatura nº', 'Fatura registada em', 'PDF da fatura'])
    for e in qs:
        fat = fiscal.fatura_resumo(e, request)
        w.writerow([e.id, f'{timezone.localtime(e.data_criacao):%d/%m/%Y %H:%M}',
                    e.comprador.user.get_full_name() or e.comprador.user.username, f'{e.valor_devido:.2f}'.replace('.', ','),
                    e.get_status_display(), fat['numero'] if fat else '',
                    f'{timezone.localtime(fat["registada_em"]):%d/%m/%Y}' if fat else '', (fat or {}).get('pdf_url') or ''])
    return r


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_bende(request):
    """O que o Bende tem de faturar no mês: mensalidades pagas e comissões por loja."""
    erro = _exige_admin(request, 'gerir_faturacao')
    if erro:
        return erro
    mes = _mes(request.GET.get('mes')) or timezone.localdate().replace(day=1)
    seguinte = (mes.replace(day=28) + timedelta(days=4)).replace(day=1)
    subs = (FaturaSubscricao.objects.filter(estado='paga', valor__gt=0, paga_em__date__gte=mes, paga_em__date__lt=seguinte)
            .select_related('loja', 'pos', 'plano').order_by('paga_em'))
    com = (Comissao.objects.filter(data_criacao__date__gte=mes, data_criacao__date__lt=seguinte)
           .values('loja_id', 'loja__nome', 'loja__nif').annotate(total=Sum('valor_comissao'), n=Count('id'))
           .order_by('loja__nome'))
    faturas = {fc.loja_id: fc for fc in FaturaComissoes.objects.filter(mes=mes)}
    return Response({
        'mes': f'{mes:%Y-%m}',
        'subscricoes': [{**fatura_payload(f), 'nif': getattr(f.alvo, 'nif', '')} for f in subs],
        'comissoes': [{'loja_id': c['loja_id'], 'loja_nome': c['loja__nome'], 'nif': c['loja__nif'],
                       'total': str(c['total']), 'comissoes': c['n'],
                       'fatura': fiscal.fatura_resumo(faturas.get(c['loja_id']))} for c in com],
    })


def _registar(request, obj):
    """POST regista (nº + PDF); DELETE remove. Devolve (obj, erro) — quem chama grava e envia o email."""
    if request.method == 'DELETE':
        fiscal.limpar_fatura(obj)
        return obj, None
    pdf = request.FILES.get('pdf')
    numero, msg = fiscal.validar_fatura(request.data.get('numero'), pdf)
    if msg:
        return None, Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)
    fiscal.registar_fatura(obj, numero, pdf)
    return obj, None


@api_view(['POST', 'DELETE'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
def admin_fatura_subscricao(request, fatura_id):
    erro = _exige_admin(request, 'gerir_faturacao')
    if erro:
        return erro
    f = get_object_or_404(FaturaSubscricao.objects.select_related('loja', 'pos', 'plano'), id=fatura_id)
    if f.estado != 'paga':
        return Response({'detail': 'Só se fatura uma mensalidade paga.'}, status=status.HTTP_400_BAD_REQUEST)
    f, erro = _registar(request, f)
    if erro:
        return erro
    f.save(update_fields=['fatura_numero', 'fatura_pdf', 'fatura_registada_em'])
    if request.method == 'POST':
        enviar_fatura_subscricao(f)
    return Response(fatura_payload(f))


@api_view(['POST', 'DELETE'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
def admin_fatura_comissoes(request, loja_id, mes):
    erro = _exige_admin(request, 'gerir_faturacao')
    if erro:
        return erro
    loja = get_object_or_404(Loja, id=loja_id)
    d = _mes(mes)
    if not d:
        return Response({'detail': 'Mês inválido (AAAA-MM).'}, status=status.HTTP_400_BAD_REQUEST)
    fc = FaturaComissoes.objects.filter(loja=loja, mes=d).first()
    if request.method == 'DELETE':
        if fc:
            fiscal.limpar_fatura(fc)
            fc.delete()
        return Response({'fatura': None})
    if not fc:
        _, total = documentos.comissoes_do_mes(loja, d)
        if not total:
            return Response({'detail': 'Esta loja não tem comissões nesse mês.'}, status=status.HTTP_400_BAD_REQUEST)
        fc = FaturaComissoes(loja=loja, mes=d)
    fc, erro = _registar(request, fc)
    if erro:
        return erro
    fc.save()
    enviar_fatura_comissoes(fc)
    return Response({'fatura': fiscal.fatura_resumo(fc)})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_comissoes_extrato(request, loja_id, mes):
    erro = _exige_admin(request, 'gerir_faturacao')
    if erro:
        return erro
    loja = get_object_or_404(Loja, id=loja_id)
    d = _mes(mes)
    if not d:
        return Response({'detail': 'Mês inválido (AAAA-MM).'}, status=status.HTTP_400_BAD_REQUEST)
    return _pdf(documentos.pdf_extrato_comissoes(loja, d), documentos.nome_extrato_comissoes(loja, d))
