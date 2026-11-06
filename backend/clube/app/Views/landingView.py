"""Landing page (/sobre) — página pública e edição pelo admin (perm gerir_home). Regras em utils/landing.py.
As imagens e os vídeos carregam-se pelo mesmo endpoint da home (POST /app/admin/home/imagens/, video=1)."""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from ..utils import landing as L


@api_view(['GET'])
@permission_classes([AllowAny])
def landing_publica(request):
    """GET /app/landing/ — secções publicadas (só as activas e com conteúdo)."""
    return Response(L.pagina(request))


def _admin(request):
    from .adminView import _exige_admin
    return _exige_admin(request, 'gerir_home')


def _estado(request, r=None):
    """Tudo o que o editor precisa: o rascunho em bruto (para editar), já resolvido (para mostrar como fica)."""
    from ..models import LandingPublicacao
    from ..models import HomeImagem
    from . import homeView
    r = r or L.rascunho()
    pub = LandingPublicacao.objects.select_related('publicado_por').only(
        'id', 'publicado_em', 'publicado_por__username').first()
    # imagens/vídeos do rascunho como o editor os mostra (com o estado da conversão dos vídeos)
    ids = {s.get(k) for s in r.dados for k in L.MEDIAS if s.get(k)}
    medias = {str(i): homeView._media_admin(im, request) for i, im in HomeImagem.objects.in_bulk(ids).items()} if ids else {}
    return {
        'versao': r.versao,
        'rascunho': r.dados,
        'medias': medias,
        'pagina': L.resolver(r.dados, request, todas=True),
        'alteracoes': L.tem_alteracoes(r),
        'publicacao': {'id': pub.id, 'em': pub.publicado_em,
                       'por': pub.publicado_por.username if pub.publicado_por else None} if pub else None,
        'opcoes': {'tipos': [{'tipo': t, 'nome': L.NOMES[t]} for t in L.TIPOS], 'redes': list(L.REDES),
                   'tipos_plano': list(L.TIPOS_PLANO), 'imagem_max_mb': homeView.IMAGEM_MAX_MB,
                   'video_max_mb': homeView.VIDEO_MAX_MB, 'video_max_s': homeView.VIDEO_MAX_S},
    }


def _versao(request):
    v = request.data.get('versao') if isinstance(request.data, dict) else None
    return v if isinstance(v, int) and not isinstance(v, bool) else None


def _conflito():
    return Response({'detail': 'A página foi alterada noutro sítio entretanto. Recarrega para veres a versão '
                               'mais recente.', 'codigo': 'desactualizado'}, status=status.HTTP_409_CONFLICT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_landing(request):
    """GET /app/admin/landing/"""
    erro = _admin(request)
    return erro or Response(_estado(request))


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def admin_landing_seccao(request, tipo):
    """PATCH /app/admin/landing/seccoes/<tipo>/ {versao, dados: {campo: valor…}} — só os campos enviados mudam."""
    erro = _admin(request)
    if erro:
        return erro
    if tipo not in L.TIPOS:
        return Response({'detail': 'Secção não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
    if not isinstance(request.data, dict):
        return Response({'detail': 'Dados inválidos.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        r = L.editar_seccao(tipo, request.data.get('dados'), request.user, _versao(request))
    except L.Desactualizado:
        return _conflito()
    except L.Invalido as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(_estado(request, r))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_landing_ordem(request):
    """POST /app/admin/landing/ordem/ {versao, ordem: [tipos]}"""
    erro = _admin(request)
    if erro:
        return erro
    try:
        r = L.ordenar(request.data.get('ordem') if isinstance(request.data, dict) else None,
                      request.user, _versao(request))
    except L.Desactualizado:
        return _conflito()
    except L.Invalido as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(_estado(request, r))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_landing_publicar(request):
    """POST /app/admin/landing/publicar/ {versao} — o rascunho passa a ser o que os visitantes vêem."""
    erro = _admin(request)
    if erro:
        return erro
    try:
        L.publicar(request.user, _versao(request))
    except L.Desactualizado:
        return _conflito()
    return Response(_estado(request))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_landing_descartar(request):
    """POST /app/admin/landing/descartar/ — o rascunho volta a ser igual ao publicado."""
    erro = _admin(request)
    return erro or Response(_estado(request, L.carregar(L.publicada()[1], request.user)))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_landing_padrao(request):
    """POST /app/admin/landing/padrao/ — rascunho com os textos de origem (não publica; imagens/vídeos saem)."""
    erro = _admin(request)
    return erro or Response(_estado(request, L.carregar(L.PADRAO, request.user)))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_landing_publicacoes(request):
    """GET /app/admin/landing/publicacoes/ — últimas 20."""
    from ..models import LandingPublicacao
    erro = _admin(request)
    if erro:
        return erro
    pubs = LandingPublicacao.objects.select_related('publicado_por')[:20]
    return Response([{'id': p.id, 'em': p.publicado_em, 'por': p.publicado_por.username if p.publicado_por else None}
                     for p in pubs])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_landing_restaurar(request, pub_id):
    """POST /app/admin/landing/publicacoes/<id>/restaurar/ — carrega uma publicação antiga no rascunho."""
    from ..models import LandingPublicacao
    erro = _admin(request)
    if erro:
        return erro
    pub = LandingPublicacao.objects.filter(id=pub_id).first()
    if pub is None:
        return Response({'detail': 'Publicação não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
    return Response(_estado(request, L.carregar(pub.dados, request.user)))


class _YoutubeThrottle(UserRateThrottle):
    rate = '30/min'


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([_YoutubeThrottle])
def admin_landing_youtube(request):
    """GET /app/admin/landing/youtube/?url= — id, título e autor de um vídeo (para preencher o tutorial)."""
    erro = _admin(request)
    if erro:
        return erro
    try:
        return Response(L.info_youtube(request.GET.get('url', '')))
    except L.YoutubeErro as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
