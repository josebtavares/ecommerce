from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from ..utils import home as H


@api_view(['GET'])
@permission_classes([AllowAny])
def home_publica(request):
    """GET /app/home/ — secções publicadas, já resolvidas (primeira página de cada slider)."""
    return Response(H.home(request))


@api_view(['GET'])
@permission_classes([AllowAny])
def home_seccao(request, seccao_id):
    """GET /app/home/seccao/<id>/?grupo=&offset=&limit= — páginas seguintes de um slider."""
    try:
        offset = max(int(request.GET.get('offset', 0)), 0)
        limit = min(max(int(request.GET.get('limit', 10)), 1), 50)
    except ValueError:
        return Response({'detail': 'offset/limit inválidos.'}, status=status.HTTP_400_BAD_REQUEST)
    pagina = H.pagina_publica(seccao_id, request.GET.get('grupo') or None, offset, limit, request)
    if pagina is None:
        return Response({'detail': 'Secção não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
    return Response(pagina)


# ══════════════════════════════════════════════════════════════
# ADMIN — rascunho, publicação e pré-visualização (perm gerir_home)
# ══════════════════════════════════════════════════════════════

def _admin(request):
    from .adminView import _exige_admin
    return _exige_admin(request, 'gerir_home')


def _item_admin(i, request):
    d = {'id': i.id, 'loja_id': i.loja_id, 'produto_id': i.produto_id, 'imagem_id': i.imagem_id,
         'titulo': i.titulo, 'texto': i.texto, 'link': i.link}
    if i.imagem_id:
        d['imagem_url'] = request.build_absolute_uri(i.imagem.ficheiro.url)
    if i.loja_id:
        d['loja'] = {'id': i.loja.id, 'nome': i.loja.nome, 'estado': i.loja.estado, 'ativa': i.loja.ativa}
    if i.produto_id:
        p = i.produto
        d['produto'] = {'id': p.id, 'nome': p.nome, 'ativo': p.ativo, 'loja': p.loja.nome,
                        'loja_id': p.loja_id, 'loja_ativa': p.loja.ativa}
    return d


def _refs(s):
    """Nomes das lojas/categorias referidas nos parâmetros (para o editor mostrar)."""
    from ..models import Loja, CategoriaLoja
    p = s.parametros or {}
    refs = {}
    if p.get('loja_id'):
        l = Loja.objects.filter(id=p['loja_id']).first()
        refs['loja'] = {'id': l.id, 'nome': l.nome, 'estado': l.estado, 'ativa': l.ativa} if l else None
    ids = list(p.get('categoria_ids') or []) + ([p['categoria_id']] if p.get('categoria_id') else [])
    if ids:
        cats = CategoriaLoja.objects.filter(id__in=ids).select_related('loja')
        refs['categorias'] = {c.id: {'id': c.id, 'nome': c.nome, 'loja': c.loja.nome, 'loja_ativa': c.loja.ativa}
                              for c in cats}
    return refs


def _seccao_admin(s, request):
    return {
        'id': s.id, 'tipo': s.tipo, 'tipo_nome': s.get_tipo_display(), 'titulo': s.titulo, 'subtitulo': s.subtitulo,
        'ordem': s.ordem, 'ativa': s.ativa, 'inicio': s.inicio, 'fim': s.fim,
        'fonte': s.fonte, 'criterio': s.criterio, 'parametros': s.parametros or {}, 'limite': s.limite,
        'itens': [_item_admin(i, request) for i in s.itens.all()],
        'refs': _refs(s),
        'avisos': H.avisos_seccao(s),
    }


def _seccoes_qs():
    from ..models import HomeSeccao
    return HomeSeccao.objects.prefetch_related('itens__loja', 'itens__produto__loja', 'itens__imagem')


def _estado():
    from ..models import HomePublicacao
    pub = HomePublicacao.objects.select_related('publicado_por').first()
    return {
        'publicacao': {'id': pub.id, 'em': pub.publicado_em,
                       'por': pub.publicado_por.username if pub.publicado_por else None} if pub else None,
        'tem_alteracoes': H.tem_alteracoes(),
    }


def _opcoes():
    from ..models import HomeSeccao, TipoProduto, CategoriaDestaque, Loja
    cats = sorted({c.strip().lower() for c in Loja.objects.exclude(categoria='').values_list('categoria', flat=True)})
    return {
        'tipos': [{'valor': v, 'nome': n} for v, n in HomeSeccao.TIPOS],
        'fontes': [{'valor': v, 'nome': n} for v, n in HomeSeccao.FONTES],
        'criterios_lojas': [{'valor': v, 'nome': n} for v, n in H.CRITERIOS_LOJAS.items()],
        'criterios_produtos': [{'valor': v, 'nome': n} for v, n in H.CRITERIOS_PRODUTOS.items()],
        'categorias_lojas': [{'valor': c, 'nome': H.rotulo_categoria(c)} for c in cats if c],
        'tipos_produto': [{'id': t.id, 'nome': t.nome} for t in
                          TipoProduto.objects.filter(loja__isnull=True, pos__isnull=True, ativo=True).order_by('nome')],
        'categorias_destaque': [{'id': d.categoria_id, 'nome': d.categoria.nome, 'loja': d.categoria.loja.nome}
                                for d in CategoriaDestaque.objects.filter(categoria__isnull=False)
                                .select_related('categoria__loja').order_by('ordem', 'id')],
        'limite_max': H.LIMITE_MAX,
    }


def _resposta_completa(request):
    return {'seccoes': [_seccao_admin(s, request) for s in _seccoes_qs()], **_estado(), 'opcoes': _opcoes()}


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_home(request):
    """GET /app/admin/home/ — rascunho (começa igual ao publicado), estado da publicação e opções."""
    erro = _admin(request)
    if erro:
        return erro
    H.garantir_rascunho()
    return Response(_resposta_completa(request))


def _gravar_itens(sec, itens):
    from ..models import HomeItem
    sec.itens.all().delete()
    HomeItem.objects.bulk_create([HomeItem(seccao=sec, ordem=o, **i) for o, i in enumerate(itens)])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_home_criar(request):
    """POST /app/admin/home/seccoes/ — nova secção no fim do rascunho."""
    from django.db import transaction
    from django.db.models import Max
    from ..models import HomeSeccao
    erro = _admin(request)
    if erro:
        return erro
    if HomeSeccao.objects.count() >= H.MAX_SECCOES:
        return Response({'detail': f'Máximo de {H.MAX_SECCOES} secções.'}, status=status.HTTP_400_BAD_REQUEST)
    campos, itens, msg = H.validar(request.data)
    if msg:
        return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)
    with transaction.atomic():
        ordem = (HomeSeccao.objects.aggregate(m=Max('ordem'))['m'] or 0) + 1
        sec = HomeSeccao.objects.create(ordem=ordem, **campos)
        if itens is not None:
            _gravar_itens(sec, itens)
    return Response({'seccao': _seccao_admin(_seccoes_qs().get(id=sec.id), request), **_estado()},
                    status=status.HTTP_201_CREATED)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def admin_home_seccao(request, seccao_id):
    """PATCH /app/admin/home/seccoes/<id>/ (só os campos enviados; itens substituem a lista) · DELETE."""
    from django.db import transaction
    from ..models import HomeSeccao
    erro = _admin(request)
    if erro:
        return erro
    sec = HomeSeccao.objects.filter(id=seccao_id).first()
    if sec is None:
        return Response({'detail': 'Secção não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'DELETE':
        sec.delete()
        return Response(_estado())
    campos, itens, msg = H.validar(request.data, atual=sec)
    if msg:
        return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)
    with transaction.atomic():
        for k, v in campos.items():
            setattr(sec, k, v)
        sec.save()
        if itens is not None:
            _gravar_itens(sec, itens)
    return Response({'seccao': _seccao_admin(_seccoes_qs().get(id=sec.id), request), **_estado()})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_home_duplicar(request, seccao_id):
    """POST /app/admin/home/seccoes/<id>/duplicar/ — cópia logo a seguir à original."""
    from django.db import transaction
    from django.db.models import F
    from ..models import HomeSeccao, HomeItem
    erro = _admin(request)
    if erro:
        return erro
    sec = HomeSeccao.objects.filter(id=seccao_id).first()
    if sec is None:
        return Response({'detail': 'Secção não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
    if HomeSeccao.objects.count() >= H.MAX_SECCOES:
        return Response({'detail': f'Máximo de {H.MAX_SECCOES} secções.'}, status=status.HTTP_400_BAD_REQUEST)
    with transaction.atomic():
        HomeSeccao.objects.filter(ordem__gt=sec.ordem).update(ordem=F('ordem') + 1)
        itens = list(sec.itens.all())
        sec.pk = None
        sec.ordem += 1
        sec.titulo = (sec.titulo + ' (cópia)')[:120] if sec.titulo else ''
        sec.ativa = False
        sec.save()
        HomeItem.objects.bulk_create([HomeItem(seccao=sec, ordem=i.ordem, loja_id=i.loja_id, produto_id=i.produto_id,
                                               imagem_id=i.imagem_id, titulo=i.titulo, texto=i.texto, link=i.link)
                                      for i in itens])
    return Response(_resposta_completa(request), status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_home_ordem(request):
    """POST /app/admin/home/ordem/ {ids: [...]} — todos os ids do rascunho, pela nova ordem."""
    from django.db import transaction
    from ..models import HomeSeccao
    erro = _admin(request)
    if erro:
        return erro
    ids = request.data.get('ids') if isinstance(request.data, dict) else None
    if not isinstance(ids, list) or not all(isinstance(i, int) and not isinstance(i, bool) for i in ids):
        return Response({'detail': 'Lista de ids inválida.'}, status=status.HTTP_400_BAD_REQUEST)
    with transaction.atomic():
        atuais = list(HomeSeccao.objects.select_for_update().values_list('id', flat=True))
        if sorted(ids) != sorted(atuais):
            return Response({'detail': 'A lista tem de ter todas as secções, sem repetidos. Recarrega a página.'},
                            status=status.HTTP_409_CONFLICT)
        for ordem, i in enumerate(ids):
            HomeSeccao.objects.filter(id=i).update(ordem=ordem)
    return Response(_estado())


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_home_publicar(request):
    """POST /app/admin/home/publicar/ — o rascunho passa a ser a home."""
    erro = _admin(request)
    if erro:
        return erro
    H.publicar(request.user)
    return Response(_estado())


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_home_descartar(request):
    """POST /app/admin/home/descartar/ — o rascunho volta a ser igual ao publicado."""
    erro = _admin(request)
    if erro:
        return erro
    H.carregar_rascunho(H.publicada()[1])
    return Response(_resposta_completa(request))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_home_padrao(request):
    """POST /app/admin/home/padrao/ — rascunho com o layout original (não publica)."""
    erro = _admin(request)
    if erro:
        return erro
    H.carregar_rascunho(H.layout_padrao_editavel())
    return Response(_resposta_completa(request))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_home_publicacoes(request):
    """GET /app/admin/home/publicacoes/ — últimas 20 publicações."""
    from ..models import HomePublicacao
    erro = _admin(request)
    if erro:
        return erro
    pubs = HomePublicacao.objects.select_related('publicado_por')[:20]
    return Response([{'id': p.id, 'em': p.publicado_em, 'por': p.publicado_por.username if p.publicado_por else None,
                      'seccoes': len(p.dados or [])} for p in pubs])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_home_restaurar(request, pub_id):
    """POST /app/admin/home/publicacoes/<id>/restaurar/ — carrega uma publicação antiga no rascunho."""
    from ..models import HomePublicacao
    erro = _admin(request)
    if erro:
        return erro
    pub = HomePublicacao.objects.filter(id=pub_id).first()
    if pub is None:
        return Response({'detail': 'Publicação não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
    H.carregar_rascunho(pub.dados or [])
    return Response(_resposta_completa(request))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_home_procurar(request):
    """GET /app/admin/home/procurar/?tipo=loja|produto&q=&loja_id= — para escolher itens (máx. 20)."""
    from ..models import Loja, Produto
    erro = _admin(request)
    if erro:
        return erro
    tipo = request.GET.get('tipo')
    q = (request.GET.get('q') or '').strip()[:100]
    if tipo == 'loja':
        qs = Loja.objects.all()
        if q:
            qs = qs.filter(Q(nome__icontains=q) | Q(categoria__icontains=q))
        qs = qs.order_by('-ativa', 'nome')[:20]
        return Response([{'id': l.id, 'nome': l.nome, 'categoria': l.categoria, 'estado': l.estado, 'ativa': l.ativa}
                         for l in qs])
    if tipo == 'produto':
        qs = Produto.objects.select_related('loja')
        loja_id = H._int(request.GET.get('loja_id'))
        if loja_id:
            qs = qs.filter(loja_id=loja_id)
        if q:
            qs = qs.filter(Q(nome__icontains=q) | Q(loja__nome__icontains=q))
        qs = qs.order_by('-ativo', '-loja__ativa', 'nome')[:20]
        return Response([{'id': p.id, 'nome': p.nome, 'preco': str(p.preco), 'ativo': p.ativo, 'loja': p.loja.nome,
                          'loja_id': p.loja_id, 'loja_ativa': p.loja.ativa} for p in qs])
    if tipo == 'categoria':
        from ..models import CategoriaLoja
        from django.db.models import Count
        qs = CategoriaLoja.objects.select_related('loja').annotate(_n=Count('produtos', filter=Q(produtos__ativo=True)))
        if q:
            qs = qs.filter(Q(nome__icontains=q) | Q(loja__nome__icontains=q))
        qs = qs.order_by('-loja__ativa', 'nome', 'loja__nome')[:20]
        return Response([{'id': c.id, 'nome': c.nome, 'loja': c.loja.nome, 'loja_ativa': c.loja.ativa,
                          'total_produtos': c._n} for c in qs])
    return Response({'detail': 'tipo tem de ser loja, produto ou categoria.'}, status=status.HTTP_400_BAD_REQUEST)


IMAGEM_MAX_MB = 5


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def admin_home_imagem(request):
    """POST /app/admin/home/imagens/ (multipart: ficheiro) — imagem para um banner. Devolve {id, url}."""
    from PIL import Image
    from ..models import HomeImagem
    erro = _admin(request)
    if erro:
        return erro
    f = request.FILES.get('ficheiro')
    if f is None:
        return Response({'detail': 'Escolhe uma imagem.'}, status=status.HTTP_400_BAD_REQUEST)
    if f.size > IMAGEM_MAX_MB * 1024 * 1024:
        return Response({'detail': f'A imagem tem de ter no máximo {IMAGEM_MAX_MB} MB.'}, status=status.HTTP_400_BAD_REQUEST)
    if f.name.rsplit('.', 1)[-1].lower() not in ('jpg', 'jpeg', 'png', 'webp'):
        return Response({'detail': 'Formatos aceites: JPG, PNG ou WEBP.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        img = Image.open(f)
        img.verify()
        if img.format not in ('JPEG', 'PNG', 'WEBP'):
            raise ValueError
    except Exception:
        return Response({'detail': 'O ficheiro não é uma imagem válida.'}, status=status.HTTP_400_BAD_REQUEST)
    f.seek(0)
    im = HomeImagem.objects.create(ficheiro=f)
    return Response({'id': im.id, 'url': request.build_absolute_uri(im.ficheiro.url)}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_home_preview(request):
    """GET /app/admin/home/preview/ — a home tal como fica se publicares o rascunho agora (sem cache)."""
    erro = _admin(request)
    if erro:
        return erro
    return Response(H.montar(H.rascunho_dados(), request, 'rascunho'))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_home_preview_seccao(request, seccao_id):
    """GET /app/admin/home/preview/seccao/<id>/ — páginas seguintes dos sliders na pré-visualização."""
    erro = _admin(request)
    if erro:
        return erro
    try:
        offset = max(int(request.GET.get('offset', 0)), 0)
        limit = min(max(int(request.GET.get('limit', 10)), 1), 50)
    except ValueError:
        return Response({'detail': 'offset/limit inválidos.'}, status=status.HTTP_400_BAD_REQUEST)
    rascunho = H.rascunho_dados()
    s = next((s for s in rascunho if str(s['id']) == str(seccao_id)), None)
    pagina = H.pagina_seccao(s, request.GET.get('grupo') or None, offset, limit, request,
                             vistos=H.vistos_antes(rascunho, seccao_id)) if s else None
    if pagina is None:
        return Response({'detail': 'Secção não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
    return Response(pagina)
