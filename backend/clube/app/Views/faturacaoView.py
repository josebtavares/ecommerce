"""
Faturação — documentos internos (comprovativos, extrato de comissões) e as faturas registadas.

Cliente/loja:
  GET  /app/encomenda/<id>/comprovativo/                    comprovativo da encomenda paga (PDF)
  GET  /app/subscricao/faturas/<id>/comprovativo/           comprovativo da mensalidade paga (PDF)
  GET  /app/loja/<id>/comissoes/meses/                      comissões por mês + fatura do Bende
  GET  /app/loja/<id>/comissoes/<AAAA-MM>/extrato/          extrato do mês (PDF)
Admin (gerir_faturacao):
  GET  /app/admin/faturacao/vendedores/?q=&tipo=&regime=&dados=&por_faturar=&de=&ate=&limit=&offset=
                                                            lojas (com os seus POS) e POS sem loja, paginados
  GET  /app/admin/faturacao/ficha/<loja|pos>/<id>/          ficha fiscal: dados + histórico, totais, documentos do Bende
  GET  /app/admin/faturacao/loja/<id>/vendas/?de&ate&estado&q&min&max   vendas da loja com comprovativo e fatura
  GET  /app/admin/faturacao/historico/?ref=E-1|S-1|C-1-202610           faturas registadas e anuladas do documento
  GET  /app/admin/faturacao/pesquisa/?q=                    qualquer documento, fatura, vendedor ou cliente
  GET  /app/admin/faturacao/vendas.csv?loja=&de=&ate=       vendas de uma loja com as faturas (para a DNRE)
  GET  /app/admin/faturacao/bende/?de=AAAA-MM&ate=&q=&por_faturar=   o que o Bende tem de faturar, agrupado por loja (+ POS)
  GET  /app/admin/faturacao/exportar/<loja|pos>/<id>/?de=&ate=       ZIP para a DNRE (CSVs + todos os PDFs)
  POST/DELETE /app/admin/faturacao/subscricoes/<id>/fatura/            fatura do Bende de uma mensalidade
              (substituir e DELETE pedem {motivo}: a anterior fica anulada no HistoricoFatura, nada se apaga)
  POST/DELETE /app/admin/faturacao/comissoes/<loja>/<AAAA-MM>/fatura/   fatura do Bende das comissões do mês
  GET  /app/admin/faturacao/comissoes/<loja>/<AAAA-MM>/extrato/
"""
import csv
import io
import re
import zipfile
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.core.files.storage import default_storage
from django.db.models import Count, F, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Comissao, Encomenda, FaturaComissoes, FaturaSubscricao, HistoricoFatura, Loja, UtilizadorLoja
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

def _int(v, d, maximo=None):
    try:
        n = max(0, int(v))
    except (TypeError, ValueError):
        return d
    return min(n, maximo) if maximo else n


def _paginar(request, itens, limite=20):
    """?limit=&offset= sobre uma lista ou queryset → (pagina, count)."""
    limit = _int(request.GET.get('limit'), limite, 100) or limite
    offset = _int(request.GET.get('offset'), 0)
    total = len(itens) if isinstance(itens, list) else itens.count()
    return itens[offset:offset + limit], total


def _datas(request):
    """?de=&ate= opcionais (AAAA-MM-DD). Devolve (de, ate, erro)."""
    try:
        de = date.fromisoformat(request.GET['de']) if request.GET.get('de') else None
        ate = date.fromisoformat(request.GET['ate']) if request.GET.get('ate') else None
    except ValueError:
        return None, None, Response({'detail': 'Datas inválidas.'}, status=status.HTTP_400_BAD_REQUEST)
    return de, ate, None


def _dono(obj):
    u = obj.dono.user
    return {'nome': u.get_full_name() or u.username, 'email': u.email, 'telefone': obj.dono.telefone}


def _incompletos():
    return Q(nif='') | Q(regime_fiscal='') | Q(dados_fiscais_aceites_em__isnull=True)


def _vendedor_base(obj, tipo):
    d = {'tipo': tipo, 'id': obj.id, 'nome': obj.nome, 'dono': _dono(obj), **fiscal.dados_fiscais_payload(obj)}
    if tipo == 'pos':
        d['codigo_pos'] = obj.codigo_pos
        d['loja'] = {'id': obj.loja_vinculada_id, 'nome': obj.loja_vinculada.nome} if obj.loja_vinculada_id else None
    else:
        d['estado'] = obj.estado
    return d


def _vendas_filtro(de, ate, prefixo='encomendas__'):
    f = Q(**{f'{prefixo}status__in': fiscal.ESTADOS_FATURAVEIS})
    if de:
        f &= Q(**{f'{prefixo}data_criacao__date__gte': de})
    if ate:
        f &= Q(**{f'{prefixo}data_criacao__date__lte': ate})
    return f


def _contar(qs, campo):
    n = {}
    for v in qs.values_list(campo, flat=True):
        n[v] = n.get(v, 0) + 1
    return n


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_vendedores(request):
    """
    Lojas (cada uma com os seus POS) e POS sem loja, paginados.
    ?q= nome, NIF, código POS, email/nome/telefone do dono (procura também nos POS de cada loja)
    ?tipo=loja|pos  ?regime=particular|atividade  ?dados=completos|incompletos  ?por_faturar=1  ?de=&ate= (vendas)
    """
    erro = _exige_admin(request, 'gerir_faturacao')
    if erro:
        return erro
    de, ate, erro = _datas(request)
    if erro:
        return erro
    q = (request.GET.get('q') or '').strip()
    tipo = request.GET.get('tipo') or ''
    regime = request.GET.get('regime') or ''
    dados = request.GET.get('dados') or ''
    por_faturar = request.GET.get('por_faturar') in ('1', 'true')

    vendas = _vendas_filtro(de, ate)
    lojas = (Loja.objects.exclude(estado='pendente')
             .annotate(vendas=Count('encomendas', filter=vendas),
                       faturadas=Count('encomendas', filter=vendas & Q(encomendas__fatura_registada_em__isnull=False))))
    poss = ConfiguracaoPOS.objects.filter(ativo=True)
    if q:
        pessoa = (Q(dono__user__email__icontains=q) | Q(dono__user__username__icontains=q) |
                  Q(dono__user__first_name__icontains=q) | Q(dono__user__last_name__icontains=q) |
                  Q(dono__telefone__icontains=q))
        ids_pos = ConfiguracaoPOS.objects.filter(
            Q(nome__icontains=q) | Q(nif__icontains=q) | Q(codigo_pos__icontains=q) | pessoa).values('id')
        lojas = lojas.filter(id__in=Loja.objects.filter(
            Q(nome__icontains=q) | Q(nif__icontains=q) | pessoa | Q(pos_vinculados__id__in=ids_pos)).values('id'))
        poss = poss.filter(id__in=ids_pos)
    if regime in fiscal.REGIMES_VALIDOS:
        lojas, poss = lojas.filter(regime_fiscal=regime), poss.filter(regime_fiscal=regime)
    if dados == 'incompletos':      # a loja ou algum dos seus POS
        pos_inc = ConfiguracaoPOS.objects.filter(_incompletos(), ativo=True, loja_vinculada__isnull=False)
        lojas = lojas.filter(_incompletos() | Q(id__in=pos_inc.values('loja_vinculada_id')))
        poss = poss.filter(_incompletos())
    elif dados == 'completos':
        lojas, poss = lojas.exclude(_incompletos()), poss.exclude(_incompletos())
    if por_faturar:
        lojas = lojas.filter(vendas__gt=F('faturadas'))

    if tipo == 'pos':                       # todos os POS (cada um diz a loja a que pertence)
        chaves = [(n.lower(), 'pos', i) for i, n in poss.values_list('id', 'nome')]
    else:                                   # lojas (com os seus POS) + POS sem loja
        chaves = [(n.lower(), 'loja', i) for i, n in lojas.values_list('id', 'nome')]
        if tipo != 'loja' and not por_faturar:
            chaves += [(n.lower(), 'pos', i) for i, n in
                       poss.filter(loja_vinculada__isnull=True).values_list('id', 'nome')]
    chaves.sort()
    pagina, total = _paginar(request, chaves)

    ids_l = [i for _, t, i in pagina if t == 'loja']
    ids_p = [i for _, t, i in pagina if t == 'pos']
    lojas_pg = {l.id: l for l in lojas.filter(id__in=ids_l).select_related('dono__user')}
    pos_pg = {p.id: p for p in ConfiguracaoPOS.objects.filter(id__in=ids_p).select_related('dono__user', 'loja_vinculada')}
    pos_das_lojas = {}
    for p in (ConfiguracaoPOS.objects.filter(loja_vinculada_id__in=ids_l, ativo=True)
              .select_related('dono__user', 'loja_vinculada').order_by('nome')):
        pos_das_lojas.setdefault(p.loja_vinculada_id, []).append(_vendedor_base(p, 'pos'))

    results = []
    for _, t, i in pagina:
        if t == 'loja':
            l = lojas_pg[i]
            results.append({**_vendedor_base(l, 'loja'), 'vendas': l.vendas, 'faturadas': l.faturadas,
                            'por_faturar': l.vendas - l.faturadas, 'pos': pos_das_lojas.get(i, [])})
        else:
            results.append(_vendedor_base(pos_pg[i], 'pos'))
    return Response({'count': total, 'results': results})


def _mensalidades(alvo, request):
    qs = (alvo.faturas_subscricao.filter(estado='paga', valor__gt=0)
          .select_related('loja', 'pos', 'plano').order_by('-paga_em'))
    anul = _contar(HistoricoFatura.objects.filter(fatura_subscricao__in=qs, anulada_em__isnull=False), 'fatura_subscricao_id')
    return [{**fatura_payload(f), 'referencia': f'S-{f.id}', 'fatura': fiscal.fatura_resumo(f, request),
             'anuladas': anul.get(f.id, 0)} for f in qs]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_ficha(request, tipo, id):
    """Ficha fiscal de uma loja ou POS: dados + histórico, POS/loja ligados, totais e documentos do Bende."""
    erro = _exige_admin(request, 'gerir_faturacao')
    if erro:
        return erro
    if tipo == 'loja':
        obj = get_object_or_404(Loja.objects.select_related('dono__user'), id=id)
        enc = Encomenda.objects.filter(_vendas_filtro(None, None, ''), loja=obj)
        n, fat = enc.count(), enc.filter(fatura_registada_em__isnull=False).count()
        anul_com = {f'{m:%Y-%m}': c for m, c in _contar(
            HistoricoFatura.objects.filter(tipo='comissoes', loja=obj, anulada_em__isnull=False), 'mes').items()}
        dados = {
            **_vendedor_base(obj, 'loja'),
            'pos': [_vendedor_base(p, 'pos') for p in
                    obj.pos_vinculados.filter(ativo=True).select_related('dono__user', 'loja_vinculada')],
            'totais': {'vendas': n, 'faturadas': fat, 'por_faturar': n - fat,
                       'anuladas': HistoricoFatura.objects.filter(tipo='encomenda', loja=obj, anulada_em__isnull=False).count(),
                       'valor': str(enc.aggregate(t=Sum('valor_total'))['t'] or 0)},
            'comissoes': [{**m, 'referencia': f"C-{obj.id}-{m['mes'].replace('-', '')}", 'anuladas': anul_com.get(m['mes'], 0)}
                          for m in _comissoes_por_mes(obj)],
        }
    elif tipo == 'pos':
        obj = get_object_or_404(ConfiguracaoPOS.objects.select_related('dono__user', 'loja_vinculada'), id=id)
        dados = {**_vendedor_base(obj, 'pos'), 'comissoes': []}
    else:
        return Response({'detail': 'Tipo inválido.'}, status=status.HTTP_400_BAD_REQUEST)
    dados['historico_fiscal'] = fiscal.historico_dados_fiscais(obj)
    dados['mensalidades'] = _mensalidades(obj, request)
    return Response(dados)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_loja_vendas(request, loja_id):
    """
    Vendas de uma loja com comprovativo e fatura, paginadas.
    ?de=&ate=  ?estado=faturada|por_faturar|com_anuladas  ?q= nº encomenda, nº fatura (também anuladas), cliente  ?min=&max=
    """
    erro = _exige_admin(request, 'gerir_faturacao')
    if erro:
        return erro
    loja = get_object_or_404(Loja, id=loja_id)
    de, ate, erro = _datas(request)
    if erro:
        return erro
    qs = Encomenda.objects.filter(_vendas_filtro(de, ate, ''), loja=loja)
    estado = request.GET.get('estado') or ''
    if estado == 'faturada':
        qs = qs.filter(fatura_registada_em__isnull=False)
    elif estado == 'por_faturar':
        qs = qs.filter(fatura_registada_em__isnull=True)
    elif estado == 'com_anuladas':
        qs = qs.filter(id__in=HistoricoFatura.objects.filter(loja=loja, anulada_em__isnull=False).values('encomenda_id'))
    q = (request.GET.get('q') or '').strip().lstrip('#')
    if q:
        cond = (Q(fatura_numero__icontains=q) |
                Q(id__in=HistoricoFatura.objects.filter(loja=loja, numero__icontains=q).values('encomenda_id')) |
                Q(comprador__user__email__icontains=q) | Q(comprador__user__username__icontains=q) |
                Q(comprador__user__first_name__icontains=q) | Q(comprador__user__last_name__icontains=q))
        num = re.sub(r'^[eE]-', '', q)
        if num.isdigit():
            cond |= Q(id=int(num))
        qs = qs.filter(cond)
    for campo, op in (('min', 'gte'), ('max', 'lte')):
        try:
            if request.GET.get(campo):
                qs = qs.filter(**{f'valor_total__{op}': Decimal(request.GET[campo].replace(',', '.'))})
        except InvalidOperation:
            return Response({'detail': 'Valor inválido.'}, status=status.HTTP_400_BAD_REQUEST)

    totais = qs.aggregate(valor=Sum('valor_total'), n=Count('id'),
                          faturadas=Count('id', filter=Q(fatura_registada_em__isnull=False)))
    pagina, total = _paginar(request, qs.select_related('comprador__user', 'pagamento').order_by('-data_criacao'))
    pagina = list(pagina)
    anul = _contar(HistoricoFatura.objects.filter(encomenda__in=[e.id for e in pagina], anulada_em__isnull=False), 'encomenda_id')
    results = []
    for e in pagina:
        u = e.comprador.user
        pag = getattr(e, 'pagamento', None)
        results.append({'id': e.id, 'referencia': f'E-{e.id}', 'data': e.data_criacao,
                        'cliente': {'nome': u.get_full_name() or u.username, 'email': u.email},
                        'valor': str(e.valor_devido), 'status': e.status, 'status_nome': e.get_status_display(),
                        'comprovativo': bool(pag and pag.status in ('aprovado', 'reembolsado', 'reembolsado_parcial')),
                        'fatura': fiscal.fatura_resumo(e, request), 'anuladas': anul.get(e.id, 0)})
    return Response({'count': total, 'results': results,
                     'totais': {'vendas': totais['n'], 'valor': str(totais['valor'] or 0),
                                'faturadas': totais['faturadas'], 'por_faturar': totais['n'] - totais['faturadas']}})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_historico(request):
    """?ref=E-<id> | S-<id> | C-<loja>-<AAAAMM> → todas as faturas registadas nesse documento (em vigor e anuladas)."""
    erro = _exige_admin(request, 'gerir_faturacao')
    if erro:
        return erro
    ref = (request.GET.get('ref') or '').strip().upper()
    return Response({'referencia': ref,
                     'itens': fiscal.historico_payload(HistoricoFatura.objects.filter(referencia=ref), request)})


def _res_venda(e, request):
    u = e.comprador.user
    return {'tipo': 'venda', 'referencia': f'E-{e.id}', 'titulo': f'Encomenda #{e.id}',
            'detalhe': f'{u.get_full_name() or u.username} · {e.get_status_display()}',
            'data': e.data_criacao, 'valor': str(e.valor_total), 'fatura': fiscal.fatura_resumo(e, request),
            'vendedor': {'tipo': 'loja', 'id': e.loja_id, 'nome': e.loja.nome}}


def _res_mensalidade(f, request):
    alvo = f.alvo
    return {'tipo': 'mensalidade', 'referencia': f'S-{f.id}', 'titulo': f'Mensalidade · {f.descricao}',
            'detalhe': f.get_estado_display(), 'data': f.paga_em or f.vencimento, 'valor': str(f.valor),
            'fatura': fiscal.fatura_resumo(f, request),
            'vendedor': {'tipo': 'loja' if f.loja_id else 'pos', 'id': alvo.id if alvo else None,
                         'nome': alvo.nome if alvo else ''}}


def _res_comissoes(loja, mes, request):
    fc = FaturaComissoes.objects.filter(loja=loja, mes=mes).first()
    _, total = documentos.comissoes_do_mes(loja, mes)
    return {'tipo': 'comissoes', 'referencia': f'C-{loja.id}-{mes:%Y%m}', 'titulo': f'Comissões de {mes:%m/%Y}',
            'detalhe': 'Extrato mensal', 'data': mes, 'valor': str(total or 0), 'mes': f'{mes:%Y-%m}',
            'fatura': fiscal.fatura_resumo(fc, request), 'vendedor': {'tipo': 'loja', 'id': loja.id, 'nome': loja.nome}}


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_pesquisa(request):
    """
    Pesquisa em todos os documentos de todas as lojas/POS:
    E-123 / #123 / 123 (encomenda), S-45 (mensalidade), C-12-202610 (comissões), nº de fatura (em vigor ou anulada),
    NIF, nome ou código de loja/POS, email ou nome do cliente.
    """
    erro = _exige_admin(request, 'gerir_faturacao')
    if erro:
        return erro
    q = (request.GET.get('q') or '').strip()
    if len(q) < 2:
        return Response({'count': 0, 'results': []})
    LIM = 100
    out = []
    enc = Encomenda.objects.select_related('loja', 'comprador__user')
    subs = FaturaSubscricao.objects.select_related('loja', 'pos', 'plano')

    # referências dos documentos
    m = re.fullmatch(r'(?i)(?:e-?|#)?(\d{1,9})', q)
    if m:
        out += [_res_venda(e, request) for e in enc.filter(id=int(m.group(1)))]
    m = re.fullmatch(r'(?i)s-?(\d{1,9})', q)
    if m:
        out += [_res_mensalidade(f, request) for f in subs.filter(id=int(m.group(1)))]
    m = re.fullmatch(r'(?i)c-?(\d{1,9})-(\d{4})(\d{2})', q)
    if m and 1 <= int(m.group(3)) <= 12:
        loja = Loja.objects.filter(id=int(m.group(1))).first()
        if loja:
            out.append(_res_comissoes(loja, date(int(m.group(2)), int(m.group(3)), 1), request))

    # nº de fatura em vigor
    out += [_res_venda(e, request) for e in enc.filter(fatura_numero__icontains=q)[:LIM]]
    out += [_res_mensalidade(f, request) for f in subs.filter(fatura_numero__icontains=q)[:LIM]]
    out += [_res_comissoes(fc.loja, fc.mes, request)
            for fc in FaturaComissoes.objects.filter(fatura_numero__icontains=q).select_related('loja')[:LIM]]
    # nº de fatura anulada
    for h in (HistoricoFatura.objects.filter(numero__icontains=q, anulada_em__isnull=False)
              .select_related('loja', 'pos')[:LIM]):
        alvo = h.loja or h.pos
        out.append({'tipo': 'anulada', 'referencia': h.referencia, 'titulo': f'Fatura {h.numero} (anulada)',
                    'detalhe': f'{h.get_tipo_display()} {h.referencia} · motivo: {h.motivo}', 'data': h.anulada_em,
                    'valor': None, 'fatura': None,
                    'vendedor': {'tipo': 'loja' if h.loja_id else 'pos', 'id': alvo.id if alvo else None,
                                 'nome': alvo.nome if alvo else '—'}})
    # vendedores (nome, NIF, código POS, dono)
    pessoa = (Q(dono__user__email__icontains=q) | Q(dono__user__first_name__icontains=q) |
              Q(dono__user__last_name__icontains=q) | Q(dono__telefone__icontains=q))
    for l in (Loja.objects.filter(Q(nome__icontains=q) | Q(nif__icontains=q) | pessoa)
              .exclude(estado='pendente')[:LIM]):
        out.append({'tipo': 'loja', 'referencia': f'L-{l.id}', 'titulo': l.nome, 'detalhe': f'Loja · NIF {l.nif or "—"}',
                    'data': None, 'valor': None, 'fatura': None, 'vendedor': {'tipo': 'loja', 'id': l.id, 'nome': l.nome}})
    for p in ConfiguracaoPOS.objects.filter(Q(nome__icontains=q) | Q(nif__icontains=q) | Q(codigo_pos__icontains=q) | pessoa)[:LIM]:
        out.append({'tipo': 'pos', 'referencia': f'P-{p.id}', 'titulo': nome_alvo(p), 'detalhe': f'POS · NIF {p.nif or "—"}',
                    'data': None, 'valor': None, 'fatura': None, 'vendedor': {'tipo': 'pos', 'id': p.id, 'nome': p.nome}})
    # cliente (email ou nome) → as suas compras
    if not re.fullmatch(r'[\d#\s-]+', q):
        cli = (Q(comprador__user__email__icontains=q) | Q(comprador__user__first_name__icontains=q) |
               Q(comprador__user__last_name__icontains=q) | Q(comprador__user__username__iexact=q))
        out += [_res_venda(e, request) for e in
                enc.filter(cli, status__in=fiscal.ESTADOS_FATURAVEIS).order_by('-data_criacao')[:LIM]]

    vistos, unicos = set(), []
    for r in out:
        if (r['tipo'], r['referencia']) not in vistos:
            vistos.add((r['tipo'], r['referencia']))
            unicos.append(r)
    pagina, total = _paginar(request, unicos)
    return Response({'count': total, 'results': pagina})


def _csv(linhas):
    """[[...], ...] → texto CSV com ; e BOM (o Excel abre com acentos)."""
    buf = io.StringIO()
    buf.write('﻿')
    w = csv.writer(buf, delimiter=';')
    w.writerows(linhas)
    return buf.getvalue()


def _quando(dt, fmt='%d/%m/%Y %H:%M'):
    return f'{timezone.localtime(dt):{fmt}}' if dt else ''


def _vendas_qs(loja, de, ate):
    qs = Encomenda.objects.filter(_vendas_filtro(de, ate, ''), loja=loja)
    return qs.select_related('comprador__user', 'pagamento').order_by('data_criacao')


def _linhas_vendas(loja, qs, de, ate, request):
    anuladas = {}
    for h in HistoricoFatura.objects.filter(encomenda__in=qs, anulada_em__isnull=False).order_by('anulada_em'):
        anuladas.setdefault(h.encomenda_id, []).append(f'{h.numero} ({h.motivo})')
    periodo = f'Período: {de:%d/%m/%Y} a {ate:%d/%m/%Y}' if de and ate else 'Período: desde sempre'
    linhas = [
        [f'Loja: {loja.nome}', f'NIF: {loja.nif or "—"}', f'Regime: {loja.get_regime_fiscal_display() or "—"}',
         f'Declaração aceite: {_quando(loja.dados_fiscais_aceites_em)}' if loja.dados_fiscais_aceites_em else 'Declaração: por aceitar',
         periodo],
        ['Encomenda', 'Comprovativo', 'Data', 'Cliente', 'Email do cliente', 'Valor (CVE)', 'Estado',
         'Fatura nº', 'Fatura registada em', 'PDF da fatura', 'Faturas anuladas (motivo)'],
    ]
    for e in qs:
        fat = fiscal.fatura_resumo(e, request)
        u = e.comprador.user
        linhas.append([e.id, f'E-{e.id}', _quando(e.data_criacao), u.get_full_name() or u.username, u.email,
                       f'{e.valor_devido:.2f}'.replace('.', ','), e.get_status_display(), fat['numero'] if fat else '',
                       _quando(fat['registada_em'], '%d/%m/%Y') if fat else '', (fat or {}).get('pdf_url') or '',
                       ' | '.join(anuladas.get(e.id, []))])
    return linhas


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
    r = HttpResponse(_csv(_linhas_vendas(loja, _vendas_qs(loja, de, ate), de, ate, request)),
                     content_type='text/csv; charset=utf-8')
    r['Content-Disposition'] = f'attachment; filename="vendas-{loja.id}-{de}-{ate}.csv"'
    return r


# ── Faturas do Bende, agrupadas por loja (com os seus POS) ──

def _intervalo_meses(request):
    """?de=AAAA-MM&ate=AAAA-MM (ou ?mes=) → (primeiro dia, dia 1 do mês seguinte ao último); máx. 24 meses."""
    ini = _mes(request.GET.get('de') or request.GET.get('mes')) or timezone.localdate().replace(day=1)
    fim = _mes(request.GET.get('ate') or request.GET.get('mes')) or ini
    if fim < ini:
        ini, fim = fim, ini
    if (fim.year - ini.year) * 12 + fim.month - ini.month >= 24:
        return None, None
    return ini, (fim.replace(day=28) + timedelta(days=4)).replace(day=1)


def _docs_bende(ini, fim, loja_ids=None, pos_ids=None):
    """Mensalidades pagas e comissões mensais no intervalo, por grupo ('loja', id) | ('pos', id)."""
    subs = (FaturaSubscricao.objects.filter(estado='paga', valor__gt=0, paga_em__date__gte=ini, paga_em__date__lt=fim)
            .select_related('loja', 'pos', 'pos__loja_vinculada', 'plano').order_by('paga_em'))
    com = Comissao.objects.filter(data_criacao__date__gte=ini, data_criacao__date__lt=fim)
    if loja_ids is not None:
        subs = subs.filter(Q(loja_id__in=loja_ids) | Q(pos_id__in=pos_ids or []))
        com = com.filter(loja_id__in=loja_ids)
    meses_com = {}
    for c in com.values('loja_id', 'data_criacao', 'valor_comissao'):
        mes = timezone.localtime(c['data_criacao']).date().replace(day=1)
        t = meses_com.setdefault((c['loja_id'], mes), [Decimal('0'), 0])
        t[0] += c['valor_comissao'] or 0
        t[1] += 1
    fcs = {(fc.loja_id, fc.mes): fc for fc in FaturaComissoes.objects.filter(mes__gte=ini, mes__lt=fim)}

    grupos = {}
    for f in subs:
        alvo = f.alvo
        if f.loja_id:
            chave = ('loja', f.loja_id)
        elif f.pos and f.pos.loja_vinculada_id:
            chave = ('loja', f.pos.loja_vinculada_id)
        else:
            chave = ('pos', f.pos_id)
        ref = f'S-{f.id}'
        grupos.setdefault(chave, []).append({
            'tipo': 'mensalidade', 'referencia': ref, 'id': f.id, 'titulo': f.descricao, 'alvo': nome_alvo(alvo),
            'alvo_tipo': 'loja' if f.loja_id else 'pos', 'data': f.paga_em, 'valor': str(f.valor), 'metodo_nome': f.get_metodo_display() if f.metodo else '',
            'fatura': fiscal.fatura_resumo(f), 'anuladas': 0,
            'url': f'/app/admin/faturacao/subscricoes/{f.id}/fatura/'})
    for (loja_id, mes), (total, n) in sorted(meses_com.items(), key=lambda x: x[0][1]):
        ref = f'C-{loja_id}-{mes:%Y%m}'
        grupos.setdefault(('loja', loja_id), []).append({
            'tipo': 'comissoes', 'referencia': ref, 'mes': f'{mes:%Y-%m}', 'titulo': f'Comissões de {mes:%m/%Y}',
            'data': mes, 'valor': str(total), 'comissoes': n, 'fatura': fiscal.fatura_resumo(fcs.get((loja_id, mes))),
            'anuladas': 0, 'url': f'/app/admin/faturacao/comissoes/{loja_id}/{mes:%Y-%m}/fatura/'})
    docs = [d for v in grupos.values() for d in v]
    anuladas = _contar(HistoricoFatura.objects.filter(referencia__in=[d['referencia'] for d in docs],
                                                      anulada_em__isnull=False), 'referencia')
    for d in docs:
        d['anuladas'] = anuladas.get(d['referencia'], 0)
    return grupos


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_bende(request):
    """
    O que o Bende tem de faturar: mensalidades pagas e comissões do mês, agrupadas por loja (com os seus POS)
    e POS sem loja. ?de=AAAA-MM&ate=AAAA-MM (ou ?mes=)  ?q= nome/NIF/código/dono  ?por_faturar=1  ?limit=&offset=
    """
    erro = _exige_admin(request, 'gerir_faturacao')
    if erro:
        return erro
    ini, fim = _intervalo_meses(request)
    if not ini:
        return Response({'detail': 'Escolhe no máximo 24 meses.'}, status=status.HTTP_400_BAD_REQUEST)
    grupos = _docs_bende(ini, fim)
    por_faturar = request.GET.get('por_faturar') in ('1', 'true')
    if por_faturar:
        grupos = {k: [d for d in v if not d['fatura']] for k, v in grupos.items()}
        grupos = {k: v for k, v in grupos.items() if v}

    lojas = {l.id: l for l in Loja.objects.filter(id__in=[i for t, i in grupos if t == 'loja']).select_related('dono__user')}
    poss = {p.id: p for p in ConfiguracaoPOS.objects.filter(id__in=[i for t, i in grupos if t == 'pos']).select_related('dono__user')}
    q = (request.GET.get('q') or '').strip().lower()
    itens = []
    for (t, i), docs in grupos.items():
        obj = lojas.get(i) if t == 'loja' else poss.get(i)
        if not obj:
            continue
        u = obj.dono.user
        if q and not any(q in (x or '').lower() for x in (obj.nome, obj.nif, getattr(obj, 'codigo_pos', ''), u.email,
                                                           u.get_full_name(), *(d.get('alvo', '') for d in docs))):
            continue
        itens.append({'tipo': t, 'id': i, 'nome': obj.nome, 'nif': obj.nif, 'regime_fiscal': obj.regime_fiscal,
                      'codigo_pos': getattr(obj, 'codigo_pos', None), 'dono': _dono(obj), 'documentos': docs,
                      'por_faturar': sum(1 for d in docs if not d['fatura']),
                      'valor': str(sum(Decimal(d['valor']) for d in docs))})
    itens.sort(key=lambda g: g['nome'].lower())
    totais = {'grupos': len(itens), 'documentos': sum(len(g['documentos']) for g in itens),
              'por_faturar': sum(g['por_faturar'] for g in itens),
              'valor': str(sum(Decimal(g['valor']) for g in itens))}
    pagina, total = _paginar(request, itens)
    return Response({'de': f'{ini:%Y-%m}', 'ate': f'{(fim - timedelta(days=1)):%Y-%m}', 'count': total,
                     'results': pagina, 'totais': totais})


# ── Exportar (ZIP para a DNRE) ──

MAX_VENDAS_ZIP = 400


def _nome_ficheiro(texto):
    return re.sub(r'[^\w.-]+', '_', texto or '').strip('_')[:60] or 'sem-numero'


def _juntar_pdf(zf, caminho, nome_storage, faltas):
    if not nome_storage:
        return
    try:
        with default_storage.open(nome_storage, 'rb') as f:
            zf.writestr(caminho, f.read())
    except Exception:
        faltas.append(f'{caminho} (ficheiro {nome_storage} não encontrado no armazenamento)')


def _juntar_faturas(zf, pasta, obj, faltas):
    """Fatura em vigor + anuladas do documento."""
    for h in fiscal.historico_do_documento(obj) if obj else []:
        if h.pdf:
            estado = 'anulada' if h.anulada_em else 'fatura'
            _juntar_pdf(zf, f'{pasta}/{estado}-{_nome_ficheiro(h.numero)}-{h.id}.pdf', h.pdf.name, faltas)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_exportar(request, tipo, id):
    """
    ZIP com tudo o que há de uma loja/POS no período (?de=&ate= AAAA-MM-DD; sem datas = desde sempre):
    dados fiscais (histórico), vendas (CSV + comprovativos + faturas em vigor e anuladas),
    mensalidades e comissões do Bende (comprovativos/extratos + faturas). Para entregar à DNRE.
    """
    erro = _exige_admin(request, 'gerir_faturacao')
    if erro:
        return erro
    de, ate, erro = _datas(request)
    if erro:
        return erro
    if tipo == 'loja':
        obj = get_object_or_404(Loja, id=id)
    elif tipo == 'pos':
        obj = get_object_or_404(ConfiguracaoPOS, id=id)
    else:
        return Response({'detail': 'Tipo inválido.'}, status=status.HTTP_400_BAD_REQUEST)
    vendas = _vendas_qs(obj, de, ate) if tipo == 'loja' else Encomenda.objects.none()
    n = vendas.count()
    if n > MAX_VENDAS_ZIP:
        return Response({'detail': f'O período tem {n} vendas — escolhe um período com até {MAX_VENDAS_ZIP}.'},
                        status=status.HTTP_400_BAD_REQUEST)

    faltas = []
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        hist = fiscal.historico_dados_fiscais(obj)
        zf.writestr('dados-fiscais.csv', _csv(
            [[f'{"Loja" if tipo == "loja" else "POS"}: {obj.nome}', f'NIF em vigor: {obj.nif or "—"}'],
             ['Desde', 'NIF', 'Regime', 'Nome', 'Gravado por', 'Email de quem gravou']] +
            [[_quando(h['aceites_em']), h['nif'], dict(fiscal.REGIMES).get(h['regime_fiscal'], ''), h['nome'],
              (h['alterado_por'] or {}).get('nome', ''), (h['alterado_por'] or {}).get('email', '')] for h in hist]))

        if tipo == 'loja':
            zf.writestr('vendas.csv', _csv(_linhas_vendas(obj, vendas, de, ate, request)))
            for e in vendas:
                pasta = f'vendas/E-{e.id}'
                pag = getattr(e, 'pagamento', None)
                if pag and pag.status in ('aprovado', 'reembolsado', 'reembolsado_parcial'):
                    zf.writestr(f'{pasta}/comprovativo-E-{e.id}.pdf', documentos.pdf_comprovativo_encomenda(e))
                _juntar_faturas(zf, pasta, e, faltas)

        # documentos do Bende
        subs = obj.faturas_subscricao.filter(estado='paga', valor__gt=0).select_related('loja', 'pos', 'plano')
        if de:
            subs = subs.filter(paga_em__date__gte=de)
        if ate:
            subs = subs.filter(paga_em__date__lte=ate)
        linhas = [['Documento', 'Tipo', 'Descrição', 'Data', 'Valor (CVE)', 'Fatura do Bende nº', 'Faturas anuladas']]
        for f in subs.order_by('paga_em'):
            pasta = f'bende/mensalidades/S-{f.id}'
            zf.writestr(f'{pasta}/comprovativo-S-{f.id}.pdf', documentos.pdf_comprovativo_subscricao(f))
            _juntar_faturas(zf, pasta, f, faltas)
            linhas.append([f'S-{f.id}', 'Mensalidade', f.descricao, _quando(f.paga_em), f'{f.valor:.2f}'.replace('.', ','),
                           f.fatura_numero, fiscal.historico_do_documento(f).filter(anulada_em__isnull=False).count()])
        if tipo == 'loja':
            for m in reversed(_comissoes_por_mes(obj)):
                mes = _mes(m['mes'])
                if (de and mes < de.replace(day=1)) or (ate and mes > ate):
                    continue
                pasta = f'bende/comissoes/C-{obj.id}-{mes:%Y%m}'
                zf.writestr(f'{pasta}/extrato-C-{obj.id}-{mes:%Y%m}.pdf', documentos.pdf_extrato_comissoes(obj, mes))
                fc = FaturaComissoes.objects.filter(loja=obj, mes=mes).first()
                for h in HistoricoFatura.objects.filter(tipo='comissoes', loja=obj, mes=mes):
                    if h.pdf:
                        _juntar_pdf(zf, f'{pasta}/{"anulada" if h.anulada_em else "fatura"}-{_nome_ficheiro(h.numero)}-{h.id}.pdf',
                                    h.pdf.name, faltas)
                linhas.append([f'C-{obj.id}-{mes:%Y%m}', 'Comissões do mês', f'{m["comissoes"]} venda(s)', f'{mes:%m/%Y}',
                               m['total'].replace('.', ','), fc.fatura_numero if fc else '',
                               HistoricoFatura.objects.filter(tipo='comissoes', loja=obj, mes=mes, anulada_em__isnull=False).count()])
        zf.writestr('bende/documentos-do-bende.csv', _csv(linhas))

        periodo = f'{de:%d/%m/%Y} a {ate:%d/%m/%Y}' if de and ate else (f'desde {de:%d/%m/%Y}' if de else (f'até {ate:%d/%m/%Y}' if ate else 'desde sempre'))
        leia = [
            f'Arquivo fiscal — {obj.nome} ({"loja" if tipo == "loja" else "POS"}), NIF {obj.nif or "por preencher"}',
            f'Período: {periodo}. Gerado pelo Bende a {_quando(timezone.now())}.', '',
            'dados-fiscais.csv            NIF e regime declarados ao longo do tempo (quem gravou e quando)',
            'vendas.csv                   cada venda com o nº da fatura da loja e as faturas anuladas (motivo)',
            'vendas/E-<nº>/               comprovativo de pagamento (Bende) + fatura(s) da loja (fatura-… em vigor, anulada-…)',
            'bende/mensalidades/S-<nº>/   comprovativo da mensalidade + fatura(s) do Bende',
            'bende/comissoes/C-…/         extrato mensal das comissões + fatura(s) do Bende',
            '', 'Os comprovativos e extratos são documentos internos e não substituem a fatura.',
        ]
        if faltas:
            leia += ['', 'Ficheiros em falta:'] + faltas
        zf.writestr('LEIA-ME.txt', '\r\n'.join(leia))

    nome = f'arquivo-fiscal-{tipo}-{obj.id}-{de or "inicio"}-{ate or timezone.localdate()}.zip'
    r = HttpResponse(buf.getvalue(), content_type='application/zip')
    r['Content-Disposition'] = f'attachment; filename="{nome}"'
    return r


def _registar(request, obj):
    """
    POST regista (nº + PDF; substituir pede motivo); DELETE {motivo} anula. Grava o documento e o arquivo.
    Devolve um erro (Response) ou None — quem chama envia o email.
    """
    motivo = ''
    if request.method == 'DELETE' or obj.fatura_registada_em:
        motivo, msg = fiscal.validar_motivo(request.data.get('motivo'))
        if msg:
            return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)
    if request.method == 'DELETE':
        if obj.fatura_registada_em:
            fiscal.anular_fatura(obj, request.user, motivo)
        return None
    pdf = request.FILES.get('pdf')
    numero, msg = fiscal.validar_fatura(request.data.get('numero'), pdf)
    if msg:
        return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)
    fiscal.registar_fatura(obj, numero, pdf, request.user, motivo)
    return None


@api_view(['POST', 'DELETE'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@permission_classes([IsAuthenticated])
def admin_fatura_subscricao(request, fatura_id):
    erro = _exige_admin(request, 'gerir_faturacao')
    if erro:
        return erro
    f = get_object_or_404(FaturaSubscricao.objects.select_related('loja', 'pos', 'plano'), id=fatura_id)
    if f.estado != 'paga':
        return Response({'detail': 'Só se fatura uma mensalidade paga.'}, status=status.HTTP_400_BAD_REQUEST)
    erro = _registar(request, f)
    if erro:
        return erro
    if request.method == 'POST':
        enviar_fatura_subscricao(f)
    return Response(fatura_payload(f))


@api_view(['POST', 'DELETE'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
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
    if not fc:
        if request.method == 'DELETE':
            return Response({'fatura': None})
        _, total = documentos.comissoes_do_mes(loja, d)
        if not total:
            return Response({'detail': 'Esta loja não tem comissões nesse mês.'}, status=status.HTTP_400_BAD_REQUEST)
        fc = FaturaComissoes(loja=loja, mes=d)
    erro = _registar(request, fc)
    if erro:
        return erro
    if request.method == 'DELETE':
        return Response({'fatura': None})
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
