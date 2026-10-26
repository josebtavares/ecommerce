"""
Faturação — documentos internos (comprovativos, extrato de comissões) e as faturas registadas.

Cliente/loja:
  GET  /app/encomenda/<id>/comprovativo/                    comprovativo da encomenda paga (PDF)
  GET  /app/marcacao/<id>/comprovativo/                     comprovativo da marcação paga online (PDF)
  GET  /app/subscricao/faturas/<id>/comprovativo/           comprovativo da mensalidade paga (PDF)
  GET  /app/loja/<id>/comissoes/meses/?ano=&limit=&offset=  comissões por mês + fatura do Bende (paginadas)
  GET  /app/loja/<id>/comissoes/<AAAA-MM>/vendas/?q=        as vendas do mês com a comissão (paginadas)
  GET  /app/loja/<id>/comissoes/<AAAA-MM>/extrato/          extrato do mês (PDF)
Admin (gerir_faturacao):
  GET  /app/admin/faturacao/vendedores/?q=&tipo=&regime=&dados=&por_faturar=&de=&ate=&limit=&offset=
                                                            lojas (com os seus POS) e POS sem loja, paginados
  GET  /app/admin/faturacao/ficha/<loja|pos>/<id>/          ficha fiscal: dados + histórico, totais, documentos do Bende
  GET  /app/admin/faturacao/loja/<id>/vendas/?origem=loja|marcacoes|pos&de&ate&estado&q&min&max
                                                            vendas da loja (loja online, marcações ou POS ligados) com a fatura
  GET  /app/admin/faturacao/pos/<id>/vendas/?...            contas fechadas de um POS com a fatura
  GET  /app/admin/faturacao/historico/?ref=E-1|M-1|V-1|S-1|C-1-202610   faturas registadas e anuladas do documento
  GET  /app/admin/faturacao/pesquisa/?q=&loja=|pos=         qualquer documento, fatura, vendedor ou cliente (opcionalmente de uma loja/POS)
  GET  /app/admin/faturacao/abas/?q=&limit=&offset=&fixar=   lojas e POS sem loja para as abas, com o nº por faturar
  GET  /app/admin/faturacao/vendas.csv?loja=|pos=&origem=&de=&ate=   vendas com as faturas (para a DNRE)
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
from decimal import Decimal

from django.core.files.storage import default_storage
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import (Comissao, CreditoComissao, Encomenda, FaturaComissoes, FaturaSubscricao, HistoricoFatura, Loja,
                      UtilizadorLoja)
from ..pos.models import ConfiguracaoPOS
from ..servicos.models import Marcacao
from ..utils import documentos, fiscal
from ..utils import faturas_vendas as fv
from ..utils.emails_fiscais import enviar_fatura_anulada, enviar_fatura_comissoes, enviar_fatura_subscricao
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
def marcacao_comprovativo(request, id):
    """O cliente, a equipa da loja (quem gere marcações ou a faturação) ou o admin (gerir_faturacao)."""
    m = get_object_or_404(Marcacao.objects.select_related('loja', 'cliente__user', 'profissional'), id=id)
    eh_cliente = m.cliente_id and getattr(request.user, 'utilizador', None) == m.cliente
    membro = _membro(request, m.loja)
    da_loja = membro and (membro.pode('gerir_marcacoes') or membro.pode('gerir_faturacao'))
    if not eh_cliente and not da_loja and _exige_admin(request, 'gerir_faturacao'):
        return Response({'detail': 'Sem permissão.'}, status=status.HTTP_403_FORBIDDEN)
    if not m.pago:
        return Response({'detail': 'Esta marcação não foi paga online — o comprovativo é só dos pagamentos feitos no Bende.'},
                        status=status.HTTP_400_BAD_REQUEST)
    return _pdf(documentos.pdf_comprovativo_marcacao(m), documentos.nome_comprovativo_marcacao(m))


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

def _mes_local(m):
    return timezone.localtime(m).date().replace(day=1) if hasattr(m, 'tzinfo') else m.replace(day=1)


def resumo_comissoes(total, creditos, fc):
    """
    Campos comuns de um mês de comissões. creditos = comissões devolvidas à loja depois de liquidadas (reembolsos).
    diferenca: o que a fatura registada cobre a mais do que o mês vale agora (reembolsos depois da fatura →
    nota de crédito ou substituir a fatura). None quando bate certo ou ainda não há fatura.
    """
    liquido = total - creditos
    faturado = getattr(fc, 'valor_faturado', None)
    return {'creditos': str(creditos), 'liquido': str(liquido),
            'valor_faturado': str(faturado) if faturado is not None else None,
            'diferenca': str(faturado - liquido) if faturado is not None and faturado != liquido else None}


def _creditos_por_mes(**filtro):
    """{(loja_id, mes): créditos} pelo mês da comissão a que dizem respeito."""
    from django.db.models.functions import TruncMonth
    out = {}
    for r in (CreditoComissao.objects.filter(**filtro).annotate(m=TruncMonth('comissao__data_criacao'))
              .values('loja_id', 'm').annotate(t=Sum('valor'))):
        out[(r['loja_id'], _mes_local(r['m']))] = r['t'] or Decimal('0')
    return out


def _comissoes_por_mes(loja):
    from django.db.models.functions import TruncMonth
    meses = (Comissao.objects.filter(loja=loja).annotate(m=TruncMonth('data_criacao'))
             .values('m').annotate(total=Sum('valor_comissao'), n=Count('id')).order_by('-m'))
    faturas = {fc.mes: fc for fc in FaturaComissoes.objects.filter(loja=loja)}
    creditos = _creditos_por_mes(loja=loja)
    out = []
    for r in meses:
        mes = _mes_local(r['m'])
        fc = faturas.get(mes)
        out.append({'mes': f'{mes:%Y-%m}', 'total': str(r['total']), 'comissoes': r['n'],
                    'fatura': fiscal.fatura_resumo(fc),
                    **resumo_comissoes(r['total'] or Decimal('0'), creditos.get((loja.id, mes), Decimal('0')), fc)})
    return out


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loja_comissoes_meses(request, loja_id):
    loja = get_object_or_404(Loja, id=loja_id)
    m = _membro(request, loja)
    if not m or not m.pode('ver_subscricao'):
        return Response({'detail': 'Sem permissão.'}, status=status.HTTP_403_FORBIDDEN)
    meses = _comissoes_por_mes(loja)
    anos = sorted({m['mes'][:4] for m in meses}, reverse=True)
    if (request.GET.get('ano') or '').isdigit():
        meses = [m for m in meses if m['mes'][:4] == request.GET['ano']]
    pagina, total = _paginar(request, meses, 12)
    return Response({'meses': pagina, 'count': total, 'anos': anos})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loja_comissoes_vendas(request, loja_id, mes):
    """GET /app/loja/<id>/comissoes/<AAAA-MM>/vendas/?q=&limit=&offset= — as vendas do mês com a comissão de cada uma."""
    loja = get_object_or_404(Loja, id=loja_id)
    m = _membro(request, loja)
    if (not m or not m.pode('ver_subscricao')) and _exige_admin(request, 'gerir_faturacao'):
        return Response({'detail': 'Sem permissão.'}, status=status.HTTP_403_FORBIDDEN)
    d = _mes(mes)
    if not d:
        return Response({'detail': 'Mês inválido (AAAA-MM).'}, status=status.HTTP_400_BAD_REQUEST)
    seguinte = (d + timedelta(days=32)).replace(day=1)
    ini = timezone.make_aware(datetime.combine(d, datetime.min.time()))
    fim = timezone.make_aware(datetime.combine(seguinte, datetime.min.time()))
    qs = Comissao.objects.filter(loja=loja, data_criacao__gte=ini, data_criacao__lt=fim).annotate(cred=Sum('creditos__valor'))
    q = (request.GET.get('q') or '').strip().lstrip('#').upper().removeprefix('E-')
    if q:
        if not q.isdigit() or len(q) > 9:
            return Response({'count': 0, 'results': [], 'total': '0'})
        qs = qs.filter(encomenda_id=int(q))
    total = Comissao.objects.filter(id__in=qs.values('id')).aggregate(t=Sum('valor_comissao'))['t'] or 0
    creditos = CreditoComissao.objects.filter(comissao__in=qs.values('id')).aggregate(t=Sum('valor'))['t'] or 0
    pagina, n = _paginar(request, qs.order_by('-data_criacao', '-id'), 10)
    return Response({'count': n, 'total': str(total), 'creditos': str(creditos), 'results': [
        {'encomenda_id': c.encomenda_id, 'data': c.data_criacao.isoformat(), 'valor_encomenda': str(c.valor_encomenda),
         'percentagem': str(c.percentagem), 'valor_comissao': str(c.valor_comissao), 'credito': str(c.cred or 0),
         'estado': c.status, 'estado_nome': c.get_status_display()} for c in pagina]})


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
    """Vendas faturáveis + as que tiveram fatura registada (canceladas depois: o documento não pode sumir do arquivo)."""
    com_fatura = HistoricoFatura.objects.filter(tipo='encomenda', encomenda__isnull=False).values('encomenda_id')
    f = Q(**{f'{prefixo}status__in': fiscal.ESTADOS_FATURAVEIS}) | Q(**{f'{prefixo}id__in': com_fatura})
    if de:
        f &= Q(**{f'{prefixo}data_criacao__date__gte': de})
    if ate:
        f &= Q(**{f'{prefixo}data_criacao__date__lte': ate})
    return f


def _por_faturar(prefixo='encomendas__'):
    """Faturável e sem fatura em vigor (uma venda cancelada não fica por faturar)."""
    return Q(**{f'{prefixo}status__in': fiscal.ESTADOS_FATURAVEIS, f'{prefixo}fatura_registada_em__isnull': True})


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
                       faturadas=Count('encomendas', filter=vendas & Q(encomendas__fatura_registada_em__isnull=False)),
                       n_por_faturar=Count('encomendas', filter=vendas & _por_faturar())))
    poss = ConfiguracaoPOS.objects.all()        # inativos também: o arquivo fiscal fica
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
        pos_inc = ConfiguracaoPOS.objects.filter(_incompletos(), loja_vinculada__isnull=False)
        lojas = lojas.filter(_incompletos() | Q(id__in=pos_inc.values('loja_vinculada_id')))
        poss = poss.filter(_incompletos())
    elif dados == 'completos':
        lojas, poss = lojas.exclude(_incompletos()), poss.exclude(_incompletos())
    # marcações e contas dos POS (as dos POS ligados contam também na loja)
    marc = fv.contagens('marcacoes', 'loja_id', de=de, ate=ate)
    pos_loja = fv.contagens('pos', 'loja_id', de=de, ate=ate)
    pos_na_loja = fv.contagens('pos', 'pos_id', de=de, ate=ate, loja__isnull=False)
    pos_cont = fv.contagens('pos', 'pos_id', de=de, ate=ate, loja__isnull=True)     # as do próprio POS
    if por_faturar:
        outras = [i for d in (marc, pos_loja) for i, c in d.items() if i and c['por_faturar']]
        lojas = lojas.filter(Q(n_por_faturar__gt=0) | Q(id__in=outras))
        poss = poss.filter(id__in=[i for i, c in pos_cont.items() if c['por_faturar']])

    if tipo == 'pos':                       # todos os POS (cada um diz a loja a que pertence)
        chaves = [(n.lower(), 'pos', i) for i, n in poss.values_list('id', 'nome')]
    else:                                   # lojas (com os seus POS) + POS sem loja
        chaves = [(n.lower(), 'loja', i) for i, n in lojas.values_list('id', 'nome')]
        if tipo != 'loja':
            chaves += [(n.lower(), 'pos', i) for i, n in
                       poss.filter(loja_vinculada__isnull=True).values_list('id', 'nome')]
    chaves.sort()
    pagina, total = _paginar(request, chaves)

    ids_l = [i for _, t, i in pagina if t == 'loja']
    ids_p = [i for _, t, i in pagina if t == 'pos']
    lojas_pg = {l.id: l for l in lojas.filter(id__in=ids_l).select_related('dono__user')}
    pos_pg = {p.id: p for p in ConfiguracaoPOS.objects.filter(id__in=ids_p).select_related('dono__user', 'loja_vinculada')}
    nada = {'vendas': 0, 'faturadas': 0, 'por_faturar': 0}
    pos_das_lojas = {}
    for p in (ConfiguracaoPOS.objects.filter(loja_vinculada_id__in=ids_l)
              .select_related('dono__user', 'loja_vinculada').order_by('nome')):
        pos_das_lojas.setdefault(p.loja_vinculada_id, []).append({**_vendedor_base(p, 'pos'), **pos_na_loja.get(p.id, nada)})

    results = []
    for _, t, i in pagina:
        if t == 'loja':
            l = lojas_pg[i]
            origens = {'loja': {'vendas': l.vendas, 'faturadas': l.faturadas, 'por_faturar': l.n_por_faturar},
                       'marcacoes': marc.get(i, nada), 'pos': pos_loja.get(i, nada)}
            results.append({**_vendedor_base(l, 'loja'), **fv.somar(*({0: o} for o in origens.values()))[0],
                            'origens': origens, 'pos': pos_das_lojas.get(i, [])})
        else:
            results.append({**_vendedor_base(pos_pg[i], 'pos'), **pos_cont.get(i, nada)})
    return Response({'count': total, 'results': results})


def abas_resposta(request, itens, prioridade=None):
    """
    Abas de lojas/POS (Faturação, Subscrições): itens [{tipo, id, nome, contador, ...}] já filtrados.
    Ordena (prioridade desc — ex.: em atraso —, contador desc, nome), pagina com ?limit=&offset= (40 por omissão) e, com ?fixar=loja-12, devolve
    também esse item em 'fixo' (a aba ativa que ainda não foi carregada).
    """
    itens.sort(key=lambda i: (-(i[prioridade] if prioridade else 0), -i['contador'], i['nome'].lower(), i['tipo'], i['id']))
    pagina, total = _paginar(request, itens, 40)
    fixo = None
    alvo = request.GET.get('fixar') or ''
    if alvo:
        fixo = next((i for i in itens if f"{i['tipo']}-{i['id']}" == alvo), None)
    return Response({'count': total, 'results': pagina, 'fixo': fixo})


def procura_abas(q):
    """?q= das abas → (Q das lojas, Q dos POS): nome, NIF, código do POS (uma loja também pelos seus POS)."""
    pos = Q(nome__icontains=q) | Q(nif__icontains=q) | Q(codigo_pos__icontains=q)
    ids_pos = ConfiguracaoPOS.objects.filter(pos).values('id')
    return Q(nome__icontains=q) | Q(nif__icontains=q) | Q(pos_vinculados__id__in=ids_pos), pos


def _comissoes_por_faturar():
    """{loja_id: nº de meses com comissões e sem fatura do Bende} — agregado na base de dados."""
    from django.db.models.functions import TruncMonth
    faturadas = set(FaturaComissoes.objects.values_list('loja_id', 'mes'))
    n = {}
    for r in (Comissao.objects.order_by().annotate(m=TruncMonth('data_criacao')).values('loja_id', 'm').distinct()):
        mes = timezone.localtime(r['m']).date() if hasattr(r['m'], 'tzinfo') else r['m']
        if (r['loja_id'], mes.replace(day=1)) not in faturadas:
            n[r['loja_id']] = n.get(r['loja_id'], 0) + 1
    return n


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_abas(request):
    """
    Abas da Faturação: lojas (com os seus POS) e POS sem loja, com o nº de documentos por faturar
    (vendas da loja, marcações e contas dos POS + mensalidades pagas e comissões mensais sem fatura do Bende).
    Pendentes primeiro, depois por nome.
    ?q= nome, NIF ou código do POS  ?limit=&offset=  ?fixar=loja-12
    """
    erro = _exige_admin(request, 'gerir_faturacao')
    if erro:
        return erro
    q = (request.GET.get('q') or '').strip()
    sem_fatura = _por_faturar()
    lojas = Loja.objects.exclude(estado='pendente')
    # POS sem loja; um POS ligado só tem aba se tiver vendas dele (sem loja) por faturar
    pos_pf = fv.contagens('pos', 'pos_id', loja__isnull=True)
    poss = ConfiguracaoPOS.objects.filter(Q(loja_vinculada__isnull=True) | Q(id__in=[i for i, c in pos_pf.items() if c['por_faturar']]))
    if q:
        ql, qp = procura_abas(q)
        lojas, poss = lojas.filter(id__in=Loja.objects.filter(ql).values('id')), poss.filter(qp)
    lojas = lojas.annotate(vendas_por_faturar=Count('encomendas', filter=sem_fatura))

    bende = {}
    for loja_id, pos_loja, pos_id, n in (FaturaSubscricao.objects.filter(estado='paga', valor__gt=0, fatura_registada_em__isnull=True)
                                         .order_by().values_list('loja_id', 'pos__loja_vinculada_id', 'pos_id').annotate(n=Count('id'))):
        chave = ('loja', loja_id or pos_loja) if (loja_id or pos_loja) else ('pos', pos_id)
        bende[chave] = bende.get(chave, 0) + n
    for loja_id, n in _comissoes_por_faturar().items():
        bende[('loja', loja_id)] = bende.get(('loja', loja_id), 0) + n

    # marcações e contas dos POS por faturar (as vendidas com o POS ligado contam na loja)
    outras = fv.somar(fv.contagens('marcacoes', 'loja_id'), fv.contagens('pos', 'loja_id'))
    itens = [{'tipo': 'loja', 'id': i, 'nome': nome, 'bende_por_faturar': bende.get(('loja', i), 0),
              'vendas_por_faturar': v + outras.get(i, {}).get('por_faturar', 0)}
             for i, nome, v in lojas.values_list('id', 'nome', 'vendas_por_faturar')]
    itens += [{'tipo': 'pos', 'id': i, 'nome': nome, 'codigo_pos': c, 'bende_por_faturar': bende.get(('pos', i), 0),
               'vendas_por_faturar': pos_pf.get(i, {}).get('por_faturar', 0)}
              for i, nome, c in poss.values_list('id', 'nome', 'codigo_pos')]
    for i in itens:
        i['contador'] = i['por_faturar'] = i['vendas_por_faturar'] + i['bende_por_faturar']
    return abas_resposta(request, itens)


def _mensalidades(alvo, request):
    """Mensalidades pagas da loja (e dos seus POS) ou do POS."""
    if alvo._meta.model_name == 'loja':
        qs = FaturaSubscricao.objects.filter(Q(loja=alvo) | Q(pos__loja_vinculada=alvo))
    else:
        qs = alvo.faturas_subscricao.all()
    qs = qs.filter(estado='paga', valor__gt=0).select_related('loja', 'pos', 'plano').order_by('-paga_em')
    anul = _contar(HistoricoFatura.objects.filter(fatura_subscricao__in=qs, anulada_em__isnull=False), 'fatura_subscricao_id')
    return [{**fatura_payload(f), 'referencia': f'S-{f.id}', 'fatura': fiscal.fatura_resumo(f, request),
             'anuladas': anul.get(f.id, 0)} for f in qs]


def _origens(obj, tipo, de=None, ate=None, todas=False):
    """
    Totais por origem: loja → loja online (sempre) + marcações e POS ligados (quando há; todas=True: sempre);
    POS → as contas. de/ate: o período (dias).
    """
    out = []
    for origem in (('loja', 'marcacoes', 'pos') if tipo == 'loja' else ('pos',)):
        qs = fv.vendas(origem, de=de, ate=ate, **({'pos': obj} if tipo == 'pos' else {'loja': obj}))
        n = qs.count()
        if not n and tipo == 'loja' and origem != 'loja' and not todas and not fv.vendas(origem, loja=obj).exists():
            continue
        h_tipo, campo = fv.HISTORICO[origem]
        anul = HistoricoFatura.objects.filter(tipo=h_tipo, anulada_em__isnull=False, **{f'{campo}__in': qs.values('id')})
        out.append({'origem': origem, 'nome': fv.NOMES[origem], 'vendas': n,
                    'faturadas': qs.filter(fatura_registada_em__isnull=False).count(),
                    'por_faturar': qs.filter(fv.q_por_faturar(origem)).count(),
                    'anuladas': anul.count(), 'valor': str(fv.valor(origem, qs))})
    return out


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_ficha(request, tipo, id):
    """Ficha fiscal de uma loja ou POS: dados + histórico, POS/loja ligados, totais e documentos do Bende."""
    erro = _exige_admin(request, 'gerir_faturacao')
    if erro:
        return erro
    if tipo == 'loja':
        obj = get_object_or_404(Loja.objects.select_related('dono__user'), id=id)
        anul_com = {f'{m:%Y-%m}': c for m, c in _contar(
            HistoricoFatura.objects.filter(tipo='comissoes', loja=obj, anulada_em__isnull=False), 'mes').items()}
        dados = {
            **_vendedor_base(obj, 'loja'),
            'pos': [_vendedor_base(p, 'pos') for p in
                    obj.pos_vinculados.select_related('dono__user', 'loja_vinculada')],
            'comissoes': [{**m, 'referencia': f"C-{obj.id}-{m['mes'].replace('-', '')}", 'anuladas': anul_com.get(m['mes'], 0)}
                          for m in _comissoes_por_mes(obj)],
        }
    elif tipo == 'pos':
        obj = get_object_or_404(ConfiguracaoPOS.objects.select_related('dono__user', 'loja_vinculada'), id=id)
        dados = {**_vendedor_base(obj, 'pos'), 'comissoes': []}
    else:
        return Response({'detail': 'Tipo inválido.'}, status=status.HTTP_400_BAD_REQUEST)
    dados['origens'] = _origens(obj, tipo)
    dados['totais'] = {k: sum(o[k] for o in dados['origens']) for k in ('vendas', 'faturadas', 'por_faturar', 'anuladas')}
    dados['totais']['valor'] = str(sum(Decimal(o['valor']) for o in dados['origens']))
    dados['historico_fiscal'] = fiscal.historico_dados_fiscais(obj)
    dados['mensalidades'] = _mensalidades(obj, request)
    return Response(dados)


def vendas_filtradas(request, origem, loja=None, pos=None, todas_do_pos=False):
    """
    ?de=&ate= ?estado=faturada|por_faturar|com_anuladas|com_comprovativo ?q= ?min=&max= → (qs, erro).
    todas_do_pos: as contas do POS dos dois arquivos, com ?arquivo=pos|loja-<id>.
    """
    de, ate, erro = _datas(request)
    if erro:
        return None, erro
    qs = fv.vendas(origem, loja=loja, pos=pos, de=de, ate=ate, todas_do_pos=todas_do_pos)
    arquivo = request.GET.get('arquivo') or ''
    if todas_do_pos and arquivo == 'pos':
        qs = qs.filter(loja__isnull=True)
    elif todas_do_pos and arquivo.startswith('loja-') and arquivo[5:].isdigit():
        qs = qs.filter(loja_id=int(arquivo[5:]))
    h_tipo, campo = fv.HISTORICO[origem]
    estado = request.GET.get('estado') or ''
    if estado == 'faturada':
        qs = qs.filter(fatura_registada_em__isnull=False)
    elif estado == 'por_faturar':
        qs = qs.filter(fv.q_por_faturar(origem))
        if todas_do_pos:
            qs = qs.filter(fv.q_pos_fatura(pos))
    elif estado == 'com_anuladas':
        qs = qs.filter(id__in=HistoricoFatura.objects.filter(tipo=h_tipo, anulada_em__isnull=False).values(campo))
    qs = fv.filtrar(origem, qs, request.GET.get('q'))
    qs, msg = fv.filtrar_valor(origem, qs, request.GET.get('min'), request.GET.get('max'))
    if msg:
        return None, Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)
    return qs, None


def _lista_vendas(request, origem, loja=None, pos=None, todas_do_pos=False):
    """
    Vendas (com comprovativo e fatura) paginadas. ?de=&ate=  ?estado=faturada|por_faturar|com_anuladas
    ?q= nº da venda, nº fatura (também anuladas), cliente  ?min=&max=
    """
    qs, erro = vendas_filtradas(request, origem, loja=loja, pos=pos, todas_do_pos=todas_do_pos)
    if erro:
        return erro
    por_faturar = fv.q_por_faturar(origem) & fv.q_pos_fatura(pos) if todas_do_pos else fv.q_por_faturar(origem)
    totais = qs.aggregate(n=Count('id'), faturadas=Count('id', filter=Q(fatura_registada_em__isnull=False)),
                          por_faturar=Count('id', filter=por_faturar))
    pagina, total = _paginar(request, fv.com_relacoes(origem, qs).order_by(f'-{fv.CAMPO_DATA[origem]}', '-id'))
    pagina = list(pagina)
    anul = fv.anuladas_por(origem, [o.id for o in pagina])
    return Response({'count': total, 'origem': origem,
                     'results': [fv.linha(origem, o, request, anul.get(o.id, 0)) for o in pagina],
                     'totais': {'vendas': totais['n'], 'valor': str(fv.valor(origem, qs)),
                                'faturadas': totais['faturadas'], 'por_faturar': totais['por_faturar']}})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_loja_vendas(request, loja_id):
    """Vendas de uma loja: ?origem=loja (loja online, por omissão) | marcacoes | pos (contas dos POS ligados)."""
    erro = _exige_admin(request, 'gerir_faturacao')
    if erro:
        return erro
    loja = get_object_or_404(Loja, id=loja_id)
    origem = request.GET.get('origem') or 'loja'
    if origem not in fv.ORIGENS:
        return Response({'detail': 'Origem inválida.'}, status=status.HTTP_400_BAD_REQUEST)
    return _lista_vendas(request, origem, loja=loja)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_pos_vendas(request, pos_id):
    """Contas fechadas de um POS com a fatura (os mesmos filtros das vendas da loja)."""
    erro = _exige_admin(request, 'gerir_faturacao')
    if erro:
        return erro
    return _lista_vendas(request, 'pos', pos=get_object_or_404(ConfiguracaoPOS, id=pos_id))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_historico(request):
    """?ref=E-<id> | M-<id> | V-<id> | S-<id> | C-<loja>-<AAAAMM> → todas as faturas registadas nesse documento (em vigor e anuladas)."""
    erro = _exige_admin(request, 'gerir_faturacao')
    if erro:
        return erro
    ref = (request.GET.get('ref') or '').strip().upper()
    return Response({'referencia': ref,
                     'itens': fiscal.historico_payload(HistoricoFatura.objects.filter(referencia=ref), request)})


def _res_venda(e, request, origem='loja'):
    """Encomenda, marcação ou conta do POS (a vendida com o POS ligado abre na loja)."""
    l = fv.linha(origem, e, request)
    if origem == 'pos':
        vend = ({'tipo': 'loja', 'id': e.loja_id, 'nome': e.loja.nome} if e.loja_id
                else {'tipo': 'pos', 'id': e.pos_id, 'nome': e.pos.nome})
    else:
        vend = {'tipo': 'loja', 'id': e.loja_id, 'nome': e.loja.nome}
    detalhe = f"{l['cliente']['nome']} · {l['status_nome']}" + (f' · {e.pos.nome}' if origem == 'pos' else '')
    return {'tipo': 'venda', 'origem': origem, 'referencia': l['referencia'], 'titulo': l['titulo'], 'detalhe': detalhe,
            'data': l['data'], 'valor': l['valor'], 'fatura': l['fatura'], 'vendedor': vend}


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


def pesquisa_documentos(request, q, loja_id=None, pos_id=None):
    """Os resultados da pesquisa (sem paginar); loja_id: só esta loja e os seus POS; pos_id: só este POS."""
    LIM = 100
    out = []
    enc = Encomenda.objects.select_related('loja', 'comprador__user')
    marc = fv.base('marcacoes').select_related('loja', 'cliente__user')
    contas = fv.base('pos').select_related('mesa', 'pos', 'loja')
    subs = FaturaSubscricao.objects.select_related('loja', 'pos', 'plano')
    fcs = FaturaComissoes.objects.select_related('loja')
    hist = HistoricoFatura.objects.filter(anulada_em__isnull=False)
    lojas = Loja.objects.exclude(estado='pendente')
    poss = ConfiguracaoPOS.objects.all()
    if loja_id:             # só esta loja e os seus POS
        enc = enc.filter(loja_id=loja_id)
        marc = marc.filter(loja_id=loja_id)
        contas = contas.filter(loja_id=loja_id)
        subs = subs.filter(Q(loja_id=loja_id) | Q(pos__loja_vinculada_id=loja_id))
        fcs = fcs.filter(loja_id=loja_id)
        hist = hist.filter(Q(loja_id=loja_id) | Q(pos__loja_vinculada_id=loja_id, tipo='mensalidade'))
        lojas = lojas.none()
        poss = poss.filter(loja_vinculada_id=loja_id)
    elif pos_id:            # só este POS (mensalidades)
        enc, marc, fcs, lojas = enc.none(), marc.none(), fcs.none(), lojas.none()
        contas = contas.filter(pos_id=pos_id)
        subs = subs.filter(pos_id=pos_id)
        hist = hist.filter(pos_id=pos_id)
        poss = poss.filter(id=pos_id)

    # referências dos documentos
    m = re.fullmatch(r'(?i)(?:e-?|#)?(\d{1,9})', q)
    if m:
        out += [_res_venda(e, request) for e in enc.filter(id=int(m.group(1)))]
    m = re.fullmatch(r'(?i)m-?(\d{1,9})', q)
    if m:
        out += [_res_venda(x, request, 'marcacoes') for x in marc.filter(id=int(m.group(1)))]
    m = re.fullmatch(r'(?i)v-?(\d{1,9})', q)
    if m:
        out += [_res_venda(x, request, 'pos') for x in contas.filter(id=int(m.group(1)))]
    m = re.fullmatch(r'(?i)s-?(\d{1,9})', q)
    if m:
        out += [_res_mensalidade(f, request) for f in subs.filter(id=int(m.group(1)))]
    m = re.fullmatch(r'(?i)c-?(\d{1,9})-(\d{4})(\d{2})', q)
    if m and 1 <= int(m.group(3)) <= 12:
        loja = Loja.objects.filter(id=int(m.group(1))).first()
        if loja and not pos_id and (not loja_id or loja.id == loja_id):
            out.append(_res_comissoes(loja, date(int(m.group(2)), int(m.group(3)), 1), request))

    # nº de fatura em vigor
    out += [_res_venda(e, request) for e in enc.filter(fatura_numero__icontains=q)[:LIM]]
    out += [_res_venda(x, request, 'marcacoes') for x in marc.filter(fatura_numero__icontains=q)[:LIM]]
    out += [_res_venda(x, request, 'pos') for x in contas.filter(fatura_numero__icontains=q)[:LIM]]
    if re.fullmatch(r'\d{9}', q):          # NIF do cliente nas contas do POS
        out += [_res_venda(x, request, 'pos') for x in
                contas.filter(fv.q_faturavel('pos'), nif_cliente=q).order_by('-fechada_em')[:LIM]]
    out += [_res_mensalidade(f, request) for f in subs.filter(fatura_numero__icontains=q)[:LIM]]
    out += [_res_comissoes(fc.loja, fc.mes, request)
            for fc in fcs.filter(fatura_numero__icontains=q)[:LIM]]
    # nº de fatura anulada
    for h in hist.filter(numero__icontains=q).select_related('loja', 'pos')[:LIM]:
        alvo = h.loja or h.pos
        out.append({'tipo': 'anulada', 'referencia': h.referencia, 'titulo': f'Fatura {h.numero} (anulada)',
                    'detalhe': f'{h.get_tipo_display()} {h.referencia} · motivo: {h.motivo}', 'data': h.anulada_em,
                    'valor': None, 'fatura': None,
                    'vendedor': {'tipo': 'loja' if h.loja_id else 'pos', 'id': alvo.id if alvo else None,
                                 'nome': alvo.nome if alvo else '—'}})
    # vendedores (nome, NIF, código POS, dono)
    pessoa = (Q(dono__user__email__icontains=q) | Q(dono__user__first_name__icontains=q) |
              Q(dono__user__last_name__icontains=q) | Q(dono__telefone__icontains=q))
    for l in lojas.filter(Q(nome__icontains=q) | Q(nif__icontains=q) | pessoa)[:LIM]:
        out.append({'tipo': 'loja', 'referencia': f'L-{l.id}', 'titulo': l.nome, 'detalhe': f'Loja · NIF {l.nif or "—"}',
                    'data': None, 'valor': None, 'fatura': None, 'vendedor': {'tipo': 'loja', 'id': l.id, 'nome': l.nome}})
    for p in poss.filter(Q(nome__icontains=q) | Q(nif__icontains=q) | Q(codigo_pos__icontains=q) | pessoa)[:LIM]:
        out.append({'tipo': 'pos', 'referencia': f'P-{p.id}', 'titulo': nome_alvo(p), 'detalhe': f'POS · NIF {p.nif or "—"}',
                    'data': None, 'valor': None, 'fatura': None, 'vendedor': {'tipo': 'pos', 'id': p.id, 'nome': p.nome}})
    # cliente (email ou nome) → as suas compras
    if not re.fullmatch(r'[\d#\s-]+', q):
        cli = (Q(comprador__user__email__icontains=q) | Q(comprador__user__first_name__icontains=q) |
               Q(comprador__user__last_name__icontains=q) | Q(comprador__user__username__iexact=q))
        out += [_res_venda(e, request) for e in
                enc.filter(cli, status__in=fiscal.ESTADOS_FATURAVEIS).order_by('-data_criacao')[:LIM]]
        cli_m = (Q(cliente_nome__icontains=q) | Q(cliente__user__email__icontains=q) |
                 Q(cliente__user__first_name__icontains=q) | Q(cliente__user__last_name__icontains=q))
        out += [_res_venda(x, request, 'marcacoes') for x in
                marc.filter(cli_m, fv.q_faturavel('marcacoes')).order_by('-inicio')[:LIM]]

    vistos, unicos = set(), []
    for r in out:
        if (r['tipo'], r['referencia']) not in vistos:
            vistos.add((r['tipo'], r['referencia']))
            unicos.append(r)
    return unicos


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_pesquisa(request):
    """
    Pesquisa em todos os documentos de todas as lojas/POS (ou só de uma: ?loja=<id> inclui os seus POS, ?pos=<id>):
    E-123 / #123 / 123 (encomenda), M-12 (marcação), V-7 (conta do POS), S-45 (mensalidade), C-12-202610 (comissões),
    nº de fatura (em vigor ou anulada), NIF, nome ou código de loja/POS, email ou nome do cliente.
    """
    erro = _exige_admin(request, 'gerir_faturacao')
    if erro:
        return erro
    q = (request.GET.get('q') or '').strip()
    if len(q) < 2:
        return Response({'count': 0, 'results': []})
    unicos = pesquisa_documentos(request, q, _int(request.GET.get('loja'), None), _int(request.GET.get('pos'), None))
    pagina, total = _paginar(request, unicos)
    return Response({'count': total, 'results': pagina})


def _celula(c):
    """Texto que o Excel leria como fórmula (=, +, -, @ — ex.: um nome de cliente) leva ' à frente; números não."""
    if isinstance(c, str) and c[:1] in ('=', '+', '-', '@', '\t', '\r') and not re.fullmatch(r'-?[\d.,\s$]+', c):
        return "'" + c
    return c


def _csv(linhas):
    """[[...], ...] → texto CSV com ; e BOM (o Excel abre com acentos)."""
    buf = io.StringIO()
    buf.write('﻿')
    w = csv.writer(buf, delimiter=';')
    w.writerows([[_celula(c) for c in l] for l in linhas])
    return buf.getvalue()


def _quando(dt, fmt='%d/%m/%Y %H:%M'):
    return f'{timezone.localtime(dt):{fmt}}' if dt else ''


def _vendas_qs(origem, de, ate, loja=None, pos=None):
    qs = fv.vendas(origem, loja=loja, pos=pos, de=de, ate=ate)
    return fv.com_relacoes(origem, qs).order_by(fv.CAMPO_DATA[origem], 'id')


# 1.ª e 2.ª colunas e a do cliente, por origem (as outras são iguais)
COLUNAS_CSV = {
    'loja': ['Encomenda', 'Comprovativo', 'Data', 'Cliente', 'Email do cliente'],
    'marcacoes': ['Marcação', 'Referência', 'Dia do serviço', 'Cliente', 'Email ou telefone do cliente'],
    'pos': ['Conta', 'Referência', 'Fechada em', 'Cliente', 'Atendente'],
}


def _linhas_vendas(alvo, qs, de, ate, request, origem='loja'):
    h_tipo, campo = fv.HISTORICO[origem]
    anuladas = {}
    for h in HistoricoFatura.objects.filter(tipo=h_tipo, anulada_em__isnull=False,
                                            **{f'{campo}__in': qs.values('id')}).order_by('anulada_em'):
        anuladas.setdefault(getattr(h, campo), []).append(f'{h.numero} ({h.motivo})')
    periodo = f'Período: {de:%d/%m/%Y} a {ate:%d/%m/%Y}' if de and ate else 'Período: desde sempre'
    e_loja = alvo._meta.model_name == 'loja'
    linhas = [
        [f'{"Loja" if e_loja else "POS"}: {alvo.nome}', f'NIF: {alvo.nif or "—"}', f'Regime: {alvo.get_regime_fiscal_display() or "—"}',
         f'Declaração aceite: {_quando(alvo.dados_fiscais_aceites_em)}' if alvo.dados_fiscais_aceites_em else 'Declaração: por aceitar',
         periodo] + ([] if origem == 'loja' else [f'Vendas: {fv.NOMES[origem]}']),
        COLUNAS_CSV[origem] + ['Valor (CVE)', 'Estado', 'Fatura nº', 'Fatura registada em', 'PDF da fatura',
                               'Faturas anuladas (motivo)'] + (['POS', 'Gorjeta (CVE, fora da fatura)'] if origem == 'pos' else []),
    ]
    for o in qs:
        fat = fiscal.fatura_resumo(o, request)
        cli = fv.cliente(origem, o)
        contacto = (o.atendente_nome or '') if origem == 'pos' else cli['email']
        linhas.append([o.id, fv.referencia(origem, o), _quando(getattr(o, fv.CAMPO_DATA[origem])), cli['nome'], contacto,
                       f'{fv.valor_de(origem, o):.2f}'.replace('.', ','), fv.estado_nome(origem, o),
                       fat['numero'] if fat else '', _quando(fat['registada_em'], '%d/%m/%Y') if fat else '',
                       (fat or {}).get('pdf_url') or '', ' | '.join(anuladas.get(o.id, []))]
                      + ([o.pos.nome, f'{o.gorjeta:.2f}'.replace('.', ',')] if origem == 'pos' else []))
    return linhas


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_vendas_csv(request):
    erro = _exige_admin(request, 'gerir_faturacao')
    if erro:
        return erro
    de, ate = _periodo(request)
    origem = request.GET.get('origem') or 'loja'
    if request.GET.get('pos'):
        alvo, origem = get_object_or_404(ConfiguracaoPOS, id=request.GET['pos'] if request.GET['pos'].isdigit() else 0), 'pos'
        filtro = {'pos': alvo}
    else:
        alvo = get_object_or_404(Loja, id=request.GET.get('loja') if (request.GET.get('loja') or '').isdigit() else 0)
        filtro = {'loja': alvo}
    if not de:
        return Response({'detail': 'Datas inválidas.'}, status=status.HTTP_400_BAD_REQUEST)
    if origem not in fv.ORIGENS:
        return Response({'detail': 'Origem inválida.'}, status=status.HTTP_400_BAD_REQUEST)
    r = HttpResponse(_csv(_linhas_vendas(alvo, _vendas_qs(origem, de, ate, **filtro), de, ate, request, origem)),
                     content_type='text/csv; charset=utf-8')
    nome = {'loja': 'vendas', 'marcacoes': 'marcacoes', 'pos': 'vendas-pos'}[origem]
    r['Content-Disposition'] = f'attachment; filename="{nome}-{alvo.id}-{de}-{ate}.csv"'
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
    creditos = _creditos_por_mes(comissao__data_criacao__date__gte=ini, comissao__data_criacao__date__lt=fim,
                                 **({'loja_id__in': loja_ids} if loja_ids is not None else {}))

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
            **resumo_comissoes(total, creditos.get((loja_id, mes), Decimal('0')), fcs.get((loja_id, mes))),
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
    if por_faturar:       # por faturar: sem fatura, ou com fatura que já não bate certo (reembolsos depois)
        grupos = {k: [d for d in v if not d['fatura'] or d.get('diferenca')] for k, v in grupos.items()}
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
    return arquivo_zip(request, obj, tipo, de, ate)


def _grupos_arquivo(obj, tipo, de, ate):
    filtro = {'loja': obj} if tipo == 'loja' else {'pos': obj}
    return [(o, _vendas_qs(o, de, ate, **filtro)) for o in (fv.ORIGENS if tipo == 'loja' else ('pos',))]


def arquivo_zip(request, obj, tipo, de, ate, com_bende=True):
    """O ZIP do arquivo fiscal de uma loja/POS no período (admin e a própria loja).
    com_bende=False: sem os documentos do Bende (a equipa do POS não vê a subscrição do dono)."""
    n = sum(qs.count() for _, qs in _grupos_arquivo(obj, tipo, de, ate))
    if n > MAX_VENDAS_ZIP:
        return Response({'detail': f'O período tem {n} vendas — escolhe um período com até {MAX_VENDAS_ZIP}.'},
                        status=status.HTTP_400_BAD_REQUEST)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        escrever_arquivo(zf, obj, tipo, de, ate, com_bende, request)
    nome = f'arquivo-fiscal-{tipo}-{obj.id}-{de or "inicio"}-{ate or timezone.localdate()}.zip'
    r = HttpResponse(buf.getvalue(), content_type='application/zip')
    r['Content-Disposition'] = f'attachment; filename="{nome}"'
    return r


class _ComPrefixo:
    """Escreve num ZIP já aberto, dentro de uma pasta (a exportação da loja põe o arquivo em faturacao/)."""
    def __init__(self, zf, prefixo):
        self.zf, self.prefixo = zf, prefixo

    def writestr(self, nome, dados):
        self.zf.writestr(self.prefixo + nome, dados)


def escrever_arquivo(zf, obj, tipo, de, ate, com_bende=True, request=None, prefixo=''):
    """O conteúdo do arquivo fiscal escrito em `zf` (sem limite de vendas: decide quem chama).
    Devolve a lista dos ficheiros que faltaram no armazenamento."""
    if prefixo:
        zf = _ComPrefixo(zf, prefixo)
    grupos = _grupos_arquivo(obj, tipo, de, ate)
    vendas = grupos[0][1] if tipo == 'loja' else Encomenda.objects.none()
    faltas = []
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
    # marcações (comprovativo só das pagas online) e contas dos POS (só a fatura: o dinheiro não passa pelo Bende)
    for origem, qs in grupos:
        if origem == 'loja' or (tipo == 'loja' and not qs.exists()):
            continue
        pasta_base = 'marcacoes' if origem == 'marcacoes' else 'vendas-pos'
        zf.writestr(f'{pasta_base}.csv', _csv(_linhas_vendas(obj, qs, de, ate, request, origem)))
        for o in qs:
            pasta = f'{pasta_base}/{fv.referencia(origem, o)}'
            if origem == 'marcacoes' and o.pago:
                zf.writestr(f'{pasta}/comprovativo-M-{o.id}.pdf', documentos.pdf_comprovativo_marcacao(o))
            _juntar_faturas(zf, pasta, o, faltas)

    # documentos do Bende
    subs = (FaturaSubscricao.objects.filter(Q(loja=obj) | Q(pos__loja_vinculada=obj)) if tipo == 'loja'
            else obj.faturas_subscricao.all())
    subs = subs.filter(estado='paga', valor__gt=0).select_related('loja', 'pos', 'plano')
    if not com_bende:
        subs = subs.none()
    if de:
        subs = subs.filter(paga_em__date__gte=de)
    if ate:
        subs = subs.filter(paga_em__date__lte=ate)
    linhas = [['Documento', 'Tipo', 'Descrição', 'Data', 'Valor (CVE)', 'Fatura do Bende nº', 'Faturas anuladas']]
    for f in subs.order_by('paga_em'):
        pasta = f'bende/mensalidades/S-{f.id}'
        zf.writestr(f'{pasta}/comprovativo-S-{f.id}.pdf', documentos.pdf_comprovativo_subscricao(f))
        _juntar_faturas(zf, pasta, f, faltas)
        linhas.append([f'S-{f.id}', 'Mensalidade' + (f' ({nome_alvo(f.pos)})' if f.pos_id else ''), f.descricao, _quando(f.paga_em), f'{f.valor:.2f}'.replace('.', ','),
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
    if com_bende:
        zf.writestr('bende/documentos-do-bende.csv', _csv(linhas))

    periodo = f'{de:%d/%m/%Y} a {ate:%d/%m/%Y}' if de and ate else (f'desde {de:%d/%m/%Y}' if de else (f'até {ate:%d/%m/%Y}' if ate else 'desde sempre'))
    leia = [
        f'Arquivo fiscal — {obj.nome} ({"loja" if tipo == "loja" else "POS"}), NIF {obj.nif or "por preencher"}',
        f'Período: {periodo}. Gerado pelo Bende a {_quando(timezone.now())}.', '',
        'dados-fiscais.csv            NIF e regime declarados ao longo do tempo (quem gravou e quando)',
        'vendas.csv                   cada venda com o nº da fatura da loja e as faturas anuladas (motivo)',
        'vendas/E-<nº>/               comprovativo de pagamento (Bende) + fatura(s) da loja (fatura-… em vigor, anulada-…)',
        'marcacoes.csv, marcacoes/M-<nº>/     marcações (serviços): comprovativo (as pagas online) + fatura(s) da loja',
        'vendas-pos.csv, vendas-pos/V-<nº>/   contas fechadas do POS (os POS ligados, numa loja) com a fatura',
        'bende/mensalidades/S-<nº>/   comprovativo da mensalidade + fatura(s) do Bende',
        'bende/comissoes/C-…/         extrato mensal das comissões + fatura(s) do Bende',
        '', 'Os comprovativos e extratos são documentos internos e não substituem a fatura.',
    ]
    if faltas:
        leia += ['', 'Ficheiros em falta:'] + faltas
    zf.writestr('LEIA-ME.txt', '\r\n'.join(leia))
    return faltas


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
    try:
        if request.method == 'DELETE':
            if obj.fatura_registada_em:
                numero = obj.fatura_numero
                fiscal.anular_fatura(obj, request.user, motivo)
                enviar_fatura_anulada(obj, numero, motivo)
            return None
        pdf = request.FILES.get('pdf')
        numero, msg = fiscal.validar_fatura(request.data.get('numero'), pdf)
        if msg:
            return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)
        fiscal.registar_fatura(obj, numero, pdf, request.user, motivo)
    except fiscal.FaturaAlterada:
        return Response({'detail': 'A fatura foi alterada entretanto (outro pedido). Recarrega a página e tenta de novo.'}, status=status.HTTP_409_CONFLICT)
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
            return Response({'fatura': None, **_resumo_mes(loja, d, None)})
        _, total = documentos.comissoes_do_mes(loja, d)
        if not total:
            return Response({'detail': 'Esta loja não tem comissões nesse mês.'}, status=status.HTTP_400_BAD_REQUEST)
        fc = FaturaComissoes(loja=loja, mes=d)
    erro = _registar(request, fc)
    if erro:
        return erro
    if request.method == 'DELETE':
        return Response({'fatura': None, **_resumo_mes(loja, d, None)})
    # o que esta fatura cobre: se depois houver reembolsos, a diferença fica à vista (nota de crédito)
    fc.valor_faturado = documentos.liquido_do_mes(loja, d)
    FaturaComissoes.objects.filter(pk=fc.pk).update(valor_faturado=fc.valor_faturado)
    enviar_fatura_comissoes(fc)
    return Response({'fatura': fiscal.fatura_resumo(fc), **_resumo_mes(loja, d, fc)})


def _resumo_mes(loja, mes, fc):
    _, total = documentos.comissoes_do_mes(loja, mes)
    _, cred = documentos.creditos_do_mes(loja, mes)
    return resumo_comissoes(Decimal(total), Decimal(cred), fc)


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
