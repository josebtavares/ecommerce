"""
Devoluções e reembolsos — endpoints do cliente, da loja e da Bendi (regras em utils/devolucoes.py).

Cliente
  GET  /app/encomendas/<id>/reembolso/opcoes/      o que pode pedir agora
  POST /app/encomendas/<id>/cancelar/              { descricao? }
  POST /app/encomendas/<id>/reembolsos/            { motivo, descricao, itens: [{item_id, quantidade}] } (+ fotos)
  GET  /app/reembolsos/                            os meus pedidos
  POST /app/reembolsos/<id>/acao/                  { acao: aceitar_proposta | escalar | desistir, texto? }
Todos os participantes (cliente, loja com gerir_devolucoes, Bendi com gerir_devolucoes)
  GET  /app/reembolsos/<id>/                       detalhe + mensagens + fotos
  POST /app/reembolsos/<id>/mensagens/             { texto } (+ fotos)
  GET  /app/reembolsos/fotos/<id>/?t=              foto privada (link assinado, 1h)
Loja
  GET  /app/loja/<loja_id>/reembolsos/?grupo=novos|analise|produto|concluidos
  POST /app/loja/<loja_id>/reembolsos/<id>/acao/   { acao: aceitar | recusar | recebido, valor?, devolver_produto?,
                                                     motivo?, repor_stock? }
Bendi
  GET  /app/admin/reembolsos/?grupo=disputa|ativos|concluidos&loja_id=
  POST /app/admin/reembolsos/<id>/decidir/         { decisao: reembolsar | recusar, valor?, devolver_produto?, nota? }
"""
import json

from django.db import transaction
from django.db.models import Count, Q
from django.http import FileResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django_ratelimit.core import is_ratelimited
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from ..models import Encomenda, Loja, Reembolso, FotoReembolso, Utilizador, UtilizadorLoja
from ..utils import devolucoes as dev
from ..utils.devolucoes import ErroReembolso
from ..utils.pagination import paginar_lista

GRUPOS_LOJA = {
    'novos':      ('pedido',),
    'analise':    ('proposta', 'em_disputa'),
    'produto':    ('aguarda_produto',),
    'concluidos': ('reembolsado', 'recusado', 'cancelado'),
}
GRUPOS_ADMIN = {
    'disputa':    ('em_disputa',),
    'ativos':     dev.ATIVOS,
    'concluidos': ('reembolsado', 'recusado', 'cancelado'),
}


def _erro(e):
    return Response({'detail': e.mensagem}, status=e.status)


def _limitado(request, grupo, taxa):
    return is_ratelimited(request=request, group=f'reembolso_{grupo}', key='user', rate=taxa,
                          method=request.method, increment=True)


def _data(dt):
    return dt.isoformat() if dt else None


def _resumo(r):
    return {
        'id': r.id,
        'encomenda_id': r.encomenda_id,
        'loja_id': r.loja_id,
        'loja_nome': r.loja.nome,
        'cliente_nome': r.comprador.nome,
        'tipo': r.tipo, 'tipo_label': r.get_tipo_display(),
        'motivo': r.motivo, 'motivo_label': r.get_motivo_display(),
        'origem': r.origem,
        'estado': r.estado, 'estado_label': r.get_estado_display(),
        'valor_pedido': str(r.valor_pedido),
        'valor_entrega': str(r.valor_entrega),
        'valor_aprovado': str(r.valor_aprovado) if r.valor_aprovado is not None else None,
        'devolver_produto': r.devolver_produto,
        'prazo_resposta': _data(r.prazo_resposta) if r.estado == 'pedido' else None,
        'data_criacao': _data(r.data_criacao),
        'data_atualizacao': _data(r.data_atualizacao),
    }


def _detalhe(request, r, papel):
    u = request.user.utilizador
    fotos_por_msg = {}
    fotos_soltas = []
    for f in r.fotos.all().order_by('id'):
        d = {'id': f.id, 'url': request.build_absolute_uri(
            f'/app/reembolsos/fotos/{f.id}/?t={dev.assinar_foto(f.id, u.id)}')}
        (fotos_por_msg.setdefault(f.mensagem_id, []) if f.mensagem_id else fotos_soltas).append(d)
    nomes = {'cliente': r.comprador.nome, 'loja': r.loja.nome, 'admin': 'Bendi', 'sistema': 'Bendi'}
    return {
        **_resumo(r),
        'papel': papel,
        'descricao': r.descricao,
        'motivo_recusa': r.motivo_recusa,
        'decisao_admin': r.decisao_admin,
        'resposta_loja': r.resposta_loja,
        'data_resposta_loja': _data(r.data_resposta_loja),
        'metodo': r.metodo, 'metodo_label': r.get_metodo_display() if r.metodo else '',
        'produto_recebido_em': _data(r.produto_recebido_em),
        'stock_reposto': r.stock_reposto,
        'data_decisao': _data(r.data_decisao),
        'data_reembolso': _data(r.data_reembolso),
        'escalado_em': _data(r.escalado_em),
        'pode_escalar': papel == 'cliente' and dev.pode_escalar(r),
        'encomenda': {
            'id': r.encomenda_id,
            'status': r.encomenda.status,
            'valor_total': str(r.encomenda.valor_total),
            'tipo_entrega': r.encomenda.tipo_entrega,
            'data_criacao': _data(r.encomenda.data_criacao),
            'data_conclusao': _data(r.encomenda.data_conclusao),
            'reembolsado': str(dev.valor_reembolsado(r.encomenda)),
        },
        'itens': [{'item_id': i.item_id, 'nome': i.item.produto.nome if i.item.produto else 'Produto removido',
                   'atributos': i.item.atributos, 'quantidade': i.quantidade, 'valor': str(i.valor)}
                  for i in r.itens.select_related('item__produto')],
        'fotos': fotos_soltas,
        'mensagens': [{'id': m.id, 'papel': m.papel, 'autor': nomes.get(m.papel, ''),
                       'texto': m.texto, 'criada_em': _data(m.criada_em),
                       'fotos': fotos_por_msg.get(m.id, [])}
                      for m in r.mensagens.all()],
    }


def _ficheiros(request):
    return request.FILES.getlist('fotos') if hasattr(request, 'FILES') else []


def _itens_do_pedido(request):
    itens = request.data.get('itens')
    if isinstance(itens, str):            # multipart (com fotos): os itens vêm em JSON
        try:
            itens = json.loads(itens or '[]')
        except ValueError:
            raise ErroReembolso('Artigos inválidos.')
    if itens in (None, ''):
        return []
    if not isinstance(itens, list):
        raise ErroReembolso('Artigos inválidos.')
    return itens


def _encomenda_do_cliente(request, id):
    enc = get_object_or_404(Encomenda.objects.select_for_update(of=('self',)).select_related('loja'), id=id)
    if enc.comprador_id != request.user.utilizador.id:
        raise ErroReembolso('Sem permissão.', 403)
    return enc


def _reembolso_bloqueado(id):
    """O pedido e a encomenda dele, bloqueados (a encomenda primeiro — é a ordem das outras views)."""
    enc_id = get_object_or_404(Reembolso.objects.only('encomenda_id'), id=id).encomenda_id
    Encomenda.objects.select_for_update(of=('self',)).filter(id=enc_id).first()
    return Reembolso.objects.select_for_update(of=('self',)).select_related('encomenda', 'loja', 'comprador').get(id=id)


# ══════════════════════════════════════════════════════════════
# CLIENTE
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def opcoes(request, id):
    enc = get_object_or_404(Encomenda.objects.select_related('loja'), id=id)
    if enc.comprador_id != request.user.utilizador.id:
        return Response({'detail': 'Sem permissão.'}, status=status.HTTP_403_FORBIDDEN)
    op = dev.opcoes(enc)
    for k in ('prazo_problema', 'prazo_devolucao'):
        op[k] = _data(op[k])
    op['motivos'] = [{'valor': m, 'label': dict(Reembolso.MOTIVOS)[m]} for m in op['motivos']]
    op['politica_devolucao'] = enc.loja.politica_devolucao
    op['prazo_devolucao_dias'] = enc.loja.prazo_devolucao_dias
    return Response(op)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancelar(request, id):
    if _limitado(request, 'criar', '20/h'):
        return Response({'detail': 'Demasiados pedidos. Tenta mais tarde.'}, status=429)
    try:
        with transaction.atomic():
            enc = _encomenda_do_cliente(request, id)
            r = dev.cancelar_pelo_cliente(enc, request.user.utilizador, request.data.get('descricao', ''))
    except ErroReembolso as e:
        return _erro(e)
    if r is None:
        return Response({'encomenda_status': 'cancelado', 'reembolso': None})
    r.refresh_from_db()
    return Response({'encomenda_status': r.encomenda.status, 'reembolso': _detalhe(request, r, 'cliente')},
                    status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pedir(request, id):
    if _limitado(request, 'criar', '20/h'):
        return Response({'detail': 'Demasiados pedidos. Tenta mais tarde.'}, status=429)
    try:
        fotos = dev.preparar_fotos(_ficheiros(request))     # antes de abrir a transacção (é lento)
        itens = _itens_do_pedido(request)
        with transaction.atomic():
            enc = _encomenda_do_cliente(request, id)
            r = dev.pedir_devolucao(enc, request.user.utilizador, request.data.get('motivo'), itens,
                                    request.data.get('descricao', ''))
            dev.gravar_fotos(r, fotos, request.user.utilizador, r.mensagens.first())
    except ErroReembolso as e:
        return _erro(e)
    return Response(_detalhe(request, r, 'cliente'), status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def meus(request):
    qs = (Reembolso.objects.filter(comprador=request.user.utilizador)
          .select_related('loja', 'comprador__user').order_by('-data_criacao'))
    enc = request.GET.get('encomenda_id')
    if enc and enc.isdigit():
        qs = qs.filter(encomenda_id=int(enc))
    return paginar_lista(request, [_resumo(r) for r in qs[:500]])


ACOES_CLIENTE = {
    'aceitar_proposta': lambda r, u, d: dev.cliente_aceitar_proposta(r, u),
    'escalar':          lambda r, u, d: dev.cliente_escalar(r, u, d.get('texto', '')),
    'desistir':         lambda r, u, d: dev.cliente_desistir(r, u),
}


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def acao_cliente(request, id):
    acao = ACOES_CLIENTE.get(request.data.get('acao'))
    if not acao:
        return Response({'detail': 'Acção inválida.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        with transaction.atomic():
            r = _reembolso_bloqueado(id)
            if r.comprador_id != request.user.utilizador.id:
                raise ErroReembolso('Sem permissão.', 403)
            acao(r, request.user.utilizador, request.data)
    except ErroReembolso as e:
        return _erro(e)
    r.refresh_from_db()
    return Response(_detalhe(request, r, 'cliente'))


# ══════════════════════════════════════════════════════════════
# TODOS OS PARTICIPANTES
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def detalhe(request, id):
    r = get_object_or_404(Reembolso.objects.select_related('encomenda', 'loja', 'comprador__user'), id=id)
    papel = dev.papel(request.user.utilizador, r)
    if not papel:
        return Response({'detail': 'Pedido não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
    return Response(_detalhe(request, r, papel))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def nova_mensagem(request, id):
    if _limitado(request, 'mensagem', '60/h'):
        return Response({'detail': 'Demasiadas mensagens. Tenta mais tarde.'}, status=429)
    u = request.user.utilizador
    texto = (request.data.get('texto') or '').strip()
    try:
        r = get_object_or_404(Reembolso.objects.select_related('loja', 'comprador'), id=id)
        papel = dev.papel(u, r)
        if not papel:
            return Response({'detail': 'Pedido não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        if papel == 'admin' and r.estado != 'em_disputa':
            raise ErroReembolso('A Bendi só escreve nos pedidos em análise.', 403)
        ficheiros = _ficheiros(request)
        if not texto and not ficheiros:
            raise ErroReembolso('Escreve uma mensagem.')
        if len(texto) > dev.MAX_TEXTO:
            raise ErroReembolso(f'A mensagem é demasiado longa (máximo {dev.MAX_TEXTO} caracteres).')
        fotos = dev.preparar_fotos(ficheiros, ja_tem=r.fotos.count())
        with transaction.atomic():
            r = _reembolso_bloqueado(id)
            m = dev.mensagem(r, papel, texto, u)
            dev.gravar_fotos(r, fotos, u, m)
            r.save(update_fields=['data_atualizacao'])
        _avisar_mensagem(r, papel)
    except ErroReembolso as e:
        return _erro(e)
    return Response(_detalhe(request, r, papel), status=status.HTTP_201_CREATED)


def _avisar_mensagem(r, papel):
    if papel != 'cliente':
        dev._avisar_cliente(r, 'Nova mensagem no teu pedido', 'Tens uma nova mensagem sobre o reembolso.')
    if papel != 'loja':
        dev._avisar_loja(r, 'Nova mensagem num pedido de reembolso', 'Tens uma nova mensagem.')


@api_view(['GET'])
@authentication_classes([])          # <img src> não envia o token — a autorização vem na assinatura
@permission_classes([AllowAny])
def foto(request, id):
    lido = dev.ler_assinatura_foto(request.query_params.get('t', ''))
    if not lido or lido[0] != id:
        return Response({'detail': 'Link inválido ou expirado.'}, status=403)
    f = FotoReembolso.objects.select_related('reembolso').filter(id=id).first()
    u = Utilizador.objects.filter(id=lido[1]).select_related('user').first()
    # o acesso volta a ser verificado: quem saiu da loja deixa de ver, mesmo com o link
    if not f or not u or not u.is_active or not dev.papel(u, f.reembolso):
        return Response({'detail': 'Foto não encontrada.'}, status=404)
    armazenamento = f.ficheiro.storage
    if hasattr(armazenamento, 'bucket_name'):
        resp = HttpResponseRedirect(armazenamento.url(f.ficheiro.name))
    else:
        resp = FileResponse(armazenamento.open(f.ficheiro.name, 'rb'), content_type='image/webp')
    resp['Cache-Control'] = 'private, max-age=3600'
    resp['X-Content-Type-Options'] = 'nosniff'
    resp['Content-Disposition'] = 'inline'
    return resp


# ══════════════════════════════════════════════════════════════
# LOJA
# ══════════════════════════════════════════════════════════════

def _membro(request, loja):
    membro = UtilizadorLoja.objects.filter(loja=loja, utilizador=request.user.utilizador, ativo=True).first()
    if not membro or not membro.pode('gerir_devolucoes'):
        return None
    return membro


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lista_loja(request, loja_id):
    loja = get_object_or_404(Loja, id=loja_id)
    if not _membro(request, loja):
        return Response({'detail': 'Sem permissão: gerir_devolucoes'}, status=status.HTTP_403_FORBIDDEN)
    qs = Reembolso.objects.filter(loja=loja).select_related('loja', 'comprador__user')
    contagem = qs.aggregate(**{g: Count('id', filter=Q(estado__in=e)) for g, e in GRUPOS_LOJA.items()})
    grupo = request.GET.get('grupo')
    if grupo in GRUPOS_LOJA:
        qs = qs.filter(estado__in=GRUPOS_LOJA[grupo])
    enc = request.GET.get('encomenda_id')
    if enc and enc.isdigit():
        qs = qs.filter(encomenda_id=int(enc))
    # os que esperam pela loja primeiro, do prazo mais curto ao mais longo
    qs = qs.order_by('-data_atualizacao') if grupo == 'concluidos' else qs.order_by('prazo_resposta', '-data_criacao')
    resp = paginar_lista(request, [_resumo(r) for r in qs[:500]])
    if resp.status_code == 200:
        resp.data['contagem'] = contagem
    return resp


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def acao_loja(request, loja_id, id):
    loja = get_object_or_404(Loja, id=loja_id)
    if not _membro(request, loja):
        return Response({'detail': 'Sem permissão: gerir_devolucoes'}, status=status.HTTP_403_FORBIDDEN)
    u, d = request.user.utilizador, request.data
    try:
        with transaction.atomic():
            r = _reembolso_bloqueado(id)
            if r.loja_id != loja.id:
                raise ErroReembolso('Pedido não encontrado.', 404)
            acao = d.get('acao')
            if acao == 'aceitar':
                dev.loja_aceitar(r, u, d.get('valor'), _sim(d.get('devolver_produto')))
            elif acao == 'recusar':
                dev.loja_recusar(r, u, d.get('motivo', ''))
            elif acao == 'recebido':
                dev.loja_recebido(r, u, _sim(d.get('repor_stock')))
            else:
                raise ErroReembolso('Acção inválida.')
    except ErroReembolso as e:
        return _erro(e)
    r.refresh_from_db()
    return Response(_detalhe(request, r, 'loja'))


def _sim(v):
    return v in (True, 'true', '1', 1, 'on')


# ══════════════════════════════════════════════════════════════
# BENDI (admin)
# ══════════════════════════════════════════════════════════════

def _admin(request):
    if not request.user.is_staff or not request.user.utilizador.pode_admin('gerir_devolucoes'):
        return Response({'detail': 'Sem permissão: gerir_devolucoes'}, status=status.HTTP_403_FORBIDDEN)
    return None


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lista_admin(request):
    erro = _admin(request)
    if erro:
        return erro
    qs = Reembolso.objects.select_related('loja', 'comprador__user')
    contagem = qs.aggregate(**{g: Count('id', filter=Q(estado__in=e)) for g, e in GRUPOS_ADMIN.items()})
    grupo = request.GET.get('grupo')
    if grupo in GRUPOS_ADMIN:
        qs = qs.filter(estado__in=GRUPOS_ADMIN[grupo])
    for campo, filtro in (('loja_id', 'loja_id'), ('comprador_id', 'comprador_id'), ('encomenda_id', 'encomenda_id')):
        v = request.GET.get(campo)
        if v and v.isdigit():
            qs = qs.filter(**{filtro: int(v)})
    qs = qs.order_by('escalado_em', '-data_criacao') if grupo == 'disputa' else qs.order_by('-data_atualizacao')
    resp = paginar_lista(request, [_resumo(r) for r in qs[:500]])
    if resp.status_code == 200:
        resp.data['contagem'] = contagem
    return resp


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def metricas_admin(request):
    """
    GET /app/admin/reembolsos/metricas/?periodo=90
    Por loja: pedidos, reembolsados, recusados, valor e taxa (pedidos / encomendas pagas) — para encontrar lojas
    com problemas. Por cliente: quem pede mais (possíveis abusos).
    """
    from datetime import timedelta
    from django.db.models import Sum
    from django.utils import timezone
    from ..utils.pagination import periodo_dias
    erro = _admin(request)
    if erro:
        return erro
    dias = periodo_dias(request, padrao=90)
    desde = timezone.now() - timedelta(days=dias)
    pedidos = Reembolso.objects.filter(data_criacao__gte=desde)
    so_pedidos = pedidos.filter(origem='cliente')
    agreg = dict(
        n=Count('id'),
        reembolsados=Count('id', filter=Q(estado='reembolsado')),
        recusados=Count('id', filter=Q(estado='recusado')),
        disputas=Count('id', filter=Q(escalado_em__isnull=False)),
        valor=Sum('valor_aprovado', filter=Q(estado='reembolsado')),
    )
    pagas = dict(Encomenda.objects.filter(data_criacao__gte=desde, status__in=['pago', 'preparando', 'enviado', 'concluido'])
                 .values('loja_id').annotate(n=Count('id')).values_list('loja_id', 'n'))
    lojas = []
    for l in (pedidos.values('loja_id', 'loja__nome').annotate(**agreg).order_by('-n')[:50]):
        base = pagas.get(l['loja_id'], 0)
        lojas.append({'loja_id': l['loja_id'], 'loja_nome': l['loja__nome'], 'pedidos': l['n'],
                      'reembolsados': l['reembolsados'], 'recusados': l['recusados'], 'disputas': l['disputas'],
                      'valor': str(l['valor'] or 0), 'encomendas': base,
                      'taxa': round(l['n'] / base * 100, 1) if base else None})
    clientes = [{'utilizador_id': c['comprador_id'], 'nome': c['comprador__user__first_name'] or c['comprador__user__username'],
                 'username': c['comprador__user__username'], 'pedidos': c['n'], 'reembolsados': c['reembolsados'],
                 'recusados': c['recusados'], 'valor': str(c['valor'] or 0)}
                for c in (so_pedidos.values('comprador_id', 'comprador__user__first_name', 'comprador__user__username')
                          .annotate(**agreg).order_by('-n')[:10])]
    tot = pedidos.aggregate(**agreg)
    return Response({
        'periodo': dias,
        'total': {'pedidos': tot['n'], 'reembolsados': tot['reembolsados'], 'recusados': tot['recusados'],
                  'disputas': tot['disputas'], 'valor': str(tot['valor'] or 0)},
        'lojas': lojas,
        'clientes': clientes,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def decidir_admin(request, id):
    erro = _admin(request)
    if erro:
        return erro
    d = request.data
    try:
        with transaction.atomic():
            r = _reembolso_bloqueado(id)
            dev.admin_decidir(r, request.user.utilizador, d.get('decisao'), d.get('valor'),
                              _sim(d.get('devolver_produto')), d.get('nota', ''))
    except ErroReembolso as e:
        return _erro(e)
    r.refresh_from_db()
    return Response(_detalhe(request, r, 'admin'))
