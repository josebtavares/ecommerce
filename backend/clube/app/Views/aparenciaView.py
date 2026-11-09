"""
Aparência do site (utils/aparencia.py): fundos do login/registo e logótipo.

GET    /app/plataforma/aparencia/                      → público: o que o site mostra (null = o original)
GET    /app/admin/plataforma/aparencia/                → o editor (Admin → Definições), com os vídeos a otimizar
POST   /app/admin/plataforma/aparencia/fundo/          → multipart { qual: login|registo, ficheiro } (imagem ou vídeo)
DELETE /app/admin/plataforma/aparencia/fundo/?qual=    → repor o original (registo: volta a usar o do login)
POST   /app/admin/plataforma/aparencia/logo/           → multipart { tema: claro|escuro, ficheiro }
DELETE /app/admin/plataforma/aparencia/logo/?tema=     → repor o original
Permissão: gerir_plataforma (como o resto das Definições).
"""
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from ..utils import aparencia as A
from .adminView import _exige_admin


def _erro(msg):
    return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def aparencia_publica(request):
    return Response(A.publico(request))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_aparencia(request):
    erro = _exige_admin(request, 'gerir_plataforma')
    if erro:
        return erro
    return Response(A.admin(request))


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def admin_aparencia_fundo(request):
    from ..models import HomeImagem
    from ..utils import video
    from .homeView import EXT_IMAGEM, EXT_VIDEO, IMAGEM_MAX_MB, _medidas_imagem, _sondar_video
    erro = _exige_admin(request, 'gerir_plataforma')
    if erro:
        return erro
    qual = (request.data.get('qual') if request.method == 'POST' else request.query_params.get('qual')) or ''
    if qual not in A.FUNDOS:
        return _erro('Escolhe o fundo: login ou registo.')
    if request.method == 'DELETE':
        A.definir_fundo(qual, None)
        return Response(A.admin(request))
    f = request.FILES.get('ficheiro')
    if f is None:
        return _erro('Escolhe uma imagem ou um vídeo.')
    ext = f.name.rsplit('.', 1)[-1].lower() if '.' in f.name else ''
    if ext in EXT_VIDEO:
        if f.size > A.VIDEO_MAX_MB * 1024 * 1024:
            return _erro(f'O vídeo tem de ter no máximo {A.VIDEO_MAX_MB} MB.')
        try:
            info = _sondar_video(f)
        except video.VideoInvalido:
            return _erro('O ficheiro não é um vídeo válido.')
        if not info['largura_vista'] or not info['altura_vista']:
            return _erro('O ficheiro não é um vídeo válido.')
        if info['duracao'] > A.VIDEO_MAX_S + 0.5:
            return _erro(f'O vídeo tem de ter no máximo {A.VIDEO_MAX_S} segundos (este tem {round(info["duracao"])} s).')
        im = HomeImagem.objects.create(ficheiro=f, tipo='video', largura=info['largura_vista'],
                                       altura=info['altura_vista'], duracao=round(info['duracao'], 2))
    elif ext in EXT_IMAGEM:
        if f.size > IMAGEM_MAX_MB * 1024 * 1024:
            return _erro(f'A imagem tem de ter no máximo {IMAGEM_MAX_MB} MB.')
        try:
            largura, altura = _medidas_imagem(f)
        except Exception:
            return _erro('O ficheiro não é uma imagem válida.')
        im = HomeImagem.objects.create(ficheiro=f, tipo='imagem', largura=largura, altura=altura)
    else:
        return _erro('Formatos aceites: JPG, PNG ou WEBP (imagem) e MP4, WEBM ou MOV (vídeo).')
    A.definir_fundo(qual, im)
    return Response(A.admin(request), status=status.HTTP_201_CREATED)


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def admin_aparencia_logo(request):
    erro = _exige_admin(request, 'gerir_plataforma')
    if erro:
        return erro
    tema = (request.data.get('tema') if request.method == 'POST' else request.query_params.get('tema')) or ''
    if tema not in A.LOGOS:
        return _erro('Escolhe o logótipo: claro ou escuro.')
    if request.method == 'DELETE':
        A.definir_logo(tema, None)
        return Response(A.admin(request))
    f = request.FILES.get('ficheiro')
    if f is None:
        return _erro('Escolhe uma imagem.')
    ext = f.name.rsplit('.', 1)[-1].lower() if '.' in f.name else ''
    if ext not in ('png', 'webp', 'jpg', 'jpeg'):
        return _erro('Formatos aceites: PNG ou WEBP (de preferência com fundo transparente) ou JPG.')
    if f.size > A.LOGO_MAX_MB * 1024 * 1024:
        return _erro(f'O logótipo tem de ter no máximo {A.LOGO_MAX_MB} MB.')
    try:
        A.definir_logo(tema, f)
    except A.LogoInvalido as e:
        return _erro(str(e))
    return Response(A.admin(request), status=status.HTTP_201_CREATED)
