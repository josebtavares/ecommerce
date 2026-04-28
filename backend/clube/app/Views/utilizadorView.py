from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

import os
import requests as http_requests
import requests as google_requests

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from ..models import Utilizador
from ..Serializers.UtilizadorSerializer import (
    UtilizadorSerializer,
    UtilizadorPublicSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)

token_generator = PasswordResetTokenGenerator()

GOOGLE_CLIENT_ID     = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI  = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:8000/app/utilizador/google/callback/')
 


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def _build_user_payload(utilizador: Utilizador, request=None) -> dict:
    """
    Payload do utilizador devolvido no login e no registo.
    Alinhado com o que o frontend guarda em localStorage('user').
    """
    foto_url = None
    if utilizador.foto:
        foto_url = (
            request.build_absolute_uri(utilizador.foto.url)
            if request else utilizador.foto.url
        )
    else:
        foto_url = f"https://pub-803c78caa4b242b8b54656a45db9fb42.r2.dev/utilizadores/default.png"

    return {
        'id'             : utilizador.id,
        'username'       : utilizador.user.username,
        'email'          : utilizador.user.email,
        'first_name'     : utilizador.user.first_name,
        'last_name'      : utilizador.user.last_name,
        'telefone'       : utilizador.telefone,
        'morada'         : utilizador.morada,
        'foto'           : foto_url,
        'verificado'     : utilizador.verificado,
        'rating'         : str(utilizador.rating),
        'status'         : utilizador.status,
        'is_staff'       : utilizador.user.is_staff,        
        'role_admin'     : utilizador.role_admin,           
        'data_criacao'   : utilizador.data_criacao.strftime('%d-%m-%Y %H:%M:%S'),
    }


def _build_auth_response(utilizador: Utilizador, request=None) -> dict:
    """
    Devolve access_token, refresh_token e user —
    exactamente os campos que o frontend guarda no localStorage.
    """
    refresh = RefreshToken.for_user(utilizador.user)
    return {
        'access_token' : str(refresh.access_token),
        'refresh_token': str(refresh),
        'user'         : _build_user_payload(utilizador, request),
    }


# ══════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([AllowAny])
def utilizador_login(request):
    """
    POST /app/utilizador/login/
    Body: { username, password }
    Aceita login por username ou email.
    """
    username = (request.data.get('username') or '').strip()
    password = request.data.get('password', '')

    if not username or not password:
        return Response(
            {'detail': 'Username e password são obrigatórios.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # tenta autenticar por username ou email
    user = authenticate(request, username=username, password=password)

    if not user:
        # tenta por email
        try:
            django_user = User.objects.get(email__iexact=username)
            user = authenticate(request, username=django_user.username, password=password)
        except User.DoesNotExist:
            user = None

    if not user:
        return Response(
            {'detail': 'Credenciais inválidas.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    try:
        utilizador = user.utilizador
    except Utilizador.DoesNotExist:
        return Response(
            {'detail': 'Perfil de utilizador não encontrado.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if not utilizador.is_active:
        return Response(
            {'detail': 'Conta desactivada.'},
            status=status.HTTP_403_FORBIDDEN
        )

    return Response(_build_auth_response(utilizador, request), status=status.HTTP_200_OK)


# ══════════════════════════════════════════════════════════════
# REGISTO
# ══════════════════════════════════════════════════════════════

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([AllowAny])
def utilizador_create(request):
    """
    POST /app/utilizador/registar/
    Body (multipart): { username, email, password, first_name?, last_name?,
                        telefone?, morada?, foto? }
    Devolve o mesmo payload do login para o frontend autenticar imediatamente.
    """
    serializer = UtilizadorSerializer(data={
        'new_username'  : request.data.get('username'),
        'new_email'     : request.data.get('email'),
        'password'      : request.data.get('password'),
        'new_first_name': request.data.get('first_name', ''),
        'new_last_name' : request.data.get('last_name', ''),
        'telefone'      : request.data.get('telefone', ''),
        'morada'        : request.data.get('morada', ''),
        'foto'          : request.FILES.get('foto'),
    }, context={'request': request})

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    utilizador = serializer.save()

    # devolve auth payload para o frontend autenticar de imediato
    return Response(
        _build_auth_response(utilizador, request),
        status=status.HTTP_201_CREATED
    )


# ══════════════════════════════════════════════════════════════
# PERFIL
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def utilizador_me(request):
    """
    GET /app/utilizador/me/
    Devolve os dados do utilizador autenticado.
    """
    utilizador = get_object_or_404(Utilizador, user=request.user)
    return Response(_build_user_payload(utilizador, request), status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
def utilizador_update_me(request):
    """
    PUT/PATCH /app/utilizador/me/editar/
    Edita o perfil do utilizador autenticado.
    """
    utilizador = get_object_or_404(Utilizador, user=request.user)

    data = {
        'new_username'  : request.data.get('username'),
        'new_email'     : request.data.get('email'),
        'new_first_name': request.data.get('first_name'),
        'new_last_name' : request.data.get('last_name'),
        'password'      : request.data.get('password'),
        'telefone'      : request.data.get('telefone'),
        'morada'        : request.data.get('morada'),
        'foto'          : request.FILES.get('foto'),
    }
    # remove campos None para não sobrescrever com vazio
    data = {k: v for k, v in data.items() if v is not None}

    serializer = UtilizadorSerializer(
        utilizador, data=data, partial=True,
        context={'request': request}
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()
    return Response(_build_user_payload(utilizador, request), status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def utilizador_get(request, id):
    """
    GET /app/utilizador/<id>/
    Perfil público de outro utilizador.
    """
    utilizador = get_object_or_404(Utilizador, id=id)
    serializer = UtilizadorPublicSerializer(utilizador, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


# ══════════════════════════════════════════════════════════════
# ADMIN — listagem e gestão (só para admins da plataforma)
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def utilizador_list(request):
    """
    GET /app/utilizador/
    Lista todos os utilizadores (apenas admins da plataforma).
    """
    if not request.user.is_staff:
        return Response({'detail': 'Sem permissão.'}, status=status.HTTP_403_FORBIDDEN)

    utilizadores = Utilizador.objects.select_related('user').all()
    serializer = UtilizadorSerializer(utilizadores, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def utilizador_list_pagination(request):
    """
    GET /app/utilizador/pagination/?search=joao&offset=0&limit=20
    Lista paginada com pesquisa (apenas admins da plataforma).
    """
    if not request.user.is_staff:
        return Response({'detail': 'Sem permissão.'}, status=status.HTTP_403_FORBIDDEN)

    search = request.query_params.get('search', '').strip()

    try:
        offset = max(int(request.query_params.get('offset', 0)), 0)
        limit  = min(int(request.query_params.get('limit', 20)), 100)
        if limit <= 0:
            raise ValueError
    except ValueError:
        return Response({'detail': 'offset/limit inválidos.'}, status=status.HTTP_400_BAD_REQUEST)

    qs = Utilizador.objects.select_related('user').filter(
        Q(user__username__icontains=search) |
        Q(user__first_name__icontains=search) |
        Q(user__last_name__icontains=search) |
        Q(user__email__icontains=search) |
        Q(telefone__icontains=search)
    ).order_by('user__username')

    total   = qs.count()
    results = qs[offset: offset + limit]

    serializer = UtilizadorSerializer(results, many=True, context={'request': request})
    return Response({
        'count'      : total,
        'next_offset': offset + limit if offset + limit < total else None,
        'results'    : serializer.data,
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def utilizador_delete(request, id):
    """
    DELETE /app/utilizador/<id>/eliminar/
    Apenas admins da plataforma podem apagar utilizadores.
    """
    if not request.user.is_staff:
        return Response({'detail': 'Sem permissão.'}, status=status.HTTP_403_FORBIDDEN)

    utilizador = get_object_or_404(Utilizador, id=id)
    utilizador.user.delete()  # cascade apaga o Utilizador também
    return Response({'detail': 'Utilizador eliminado.'}, status=status.HTTP_200_OK)


# ══════════════════════════════════════════════════════════════
# PASSWORD RESET
# ══════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    """
    POST /app/utilizador/recuperar_senha/
    Envia email com link de recuperação.
    """
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data['email']

    try:
        django_user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        # não revela se o email existe ou não
        return Response(status=status.HTTP_200_OK)

    uid   = urlsafe_base64_encode(force_bytes(django_user.pk))
    token = token_generator.make_token(django_user)

    reset_link = (
        f"{settings.FRONTEND_BASE_URL}/recuperar_senha"
        f"?uid={uid}&token={token}"
    )

    send_mail(
        subject='Recuperação de palavra-passe',
        message=f'Clique no link para redefinir a sua palavra-passe:\n\n{reset_link}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
    )

    return Response(status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    """
    POST /app/utilizador/recuperar_senha/confirmar/
    Body: { uid, token, new_password }
    """
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    uid          = serializer.validated_data['uid']
    token        = serializer.validated_data['token']
    new_password = serializer.validated_data['new_password']

    try:
        user_id     = force_str(urlsafe_base64_decode(uid))
        django_user = User.objects.get(pk=user_id)
    except (ValueError, User.DoesNotExist):
        return Response({'detail': 'Link inválido.'}, status=status.HTTP_400_BAD_REQUEST)

    if not token_generator.check_token(django_user, token):
        return Response({'detail': 'Token expirado ou inválido.'}, status=status.HTTP_400_BAD_REQUEST)

    django_user.set_password(new_password)
    django_user.save()

    return Response({'detail': 'Palavra-passe actualizada com sucesso.'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def utilizador_search(request):
    """
    GET /app/utilizador/search/?q=joao
    Pesquisa utilizadores por username ou email.
    Qualquer utilizador autenticado pode usar — serve para adicionar staff.
    Devolve apenas dados públicos (id, username, nome, email).
    """
    q = request.query_params.get('q', '').strip()
    if len(q) < 2:
        return Response(
            {'detail': 'Pesquisa deve ter pelo menos 2 caracteres.'},
            status=status.HTTP_400_BAD_REQUEST
        )
 
    utilizadores = Utilizador.objects.select_related('user').filter(
        Q(user__username__icontains=q) |
        Q(user__email__icontains=q) |
        Q(user__first_name__icontains=q) |
        Q(user__last_name__icontains=q)
    ).exclude(
        user=request.user  # exclui o próprio utilizador
    ).filter(status='ativo')[:10]
 
    results = [
        {
            'id':       u.id,
            'username': u.user.username,
            'nome':     u.nome,
            'email':    u.user.email,
        }
        for u in utilizadores
    ]
    return Response(results, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def google_login_url(request):
    """
    GET /app/utilizador/google/
    Devolve o URL de autenticação do Google para o frontend redirecionar.
    """
    from urllib.parse import urlencode
    params = {
        'client_id':     GOOGLE_CLIENT_ID,
        'redirect_uri':  GOOGLE_REDIRECT_URI,
        'response_type': 'code',
        'scope':         'openid email profile',
        'access_type':   'offline',
        'prompt':        'select_account',
    }
    url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode(params)
    return Response({'url': url})
 
 
@api_view(['POST'])
@permission_classes([AllowAny])
def google_callback(request):
    """
    POST /app/utilizador/google/callback/
    Body: { code: "..." }
    Recebe o código do Google, troca por token, cria conta se não existir e devolve JWT.
    """
    code = request.data.get('code')
    if not code:
        return Response({'detail': 'Código Google em falta.'}, status=status.HTTP_400_BAD_REQUEST)
 
    # 1. Trocar código por access token
    token_resp = google_requests.post('https://oauth2.googleapis.com/token', data={
        'code':          code,
        'client_id':     GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'redirect_uri':  GOOGLE_REDIRECT_URI,
        'grant_type':    'authorization_code',
    })
 
    if token_resp.status_code != 200:
        return Response({'detail': 'Erro ao obter token do Google.'}, status=status.HTTP_400_BAD_REQUEST)
 
    access_token = token_resp.json().get('access_token')
 
    # 2. Obter dados do utilizador Google
    user_resp = google_requests.get(
        'https://www.googleapis.com/oauth2/v2/userinfo',
        headers={'Authorization': f'Bearer {access_token}'}
    )
 
    if user_resp.status_code != 200:
        return Response({'detail': 'Erro ao obter dados do Google.'}, status=status.HTTP_400_BAD_REQUEST)
 
    google_data = user_resp.json()
    email       = google_data.get('email')
    first_name  = google_data.get('given_name', '')
    last_name   = google_data.get('family_name', '')
    nome        = google_data.get('name', f'{first_name} {last_name}'.strip())
    foto_url    = google_data.get('picture', '')
    google_id   = google_data.get('id', '')
 
    if not email:
        return Response({'detail': 'Email não disponível no Google.'}, status=status.HTTP_400_BAD_REQUEST)
 
    # 3. Criar ou obter utilizador Django
    user, criado = User.objects.get_or_create(
        email=email,
        defaults={
            'username':   email.split('@')[0],
            'first_name': first_name,
            'last_name':  last_name,
        }
    )
 
    # Garantir username único
    if criado:
        base = email.split('@')[0]
        username = base
        i = 1
        while User.objects.filter(username=username).exclude(pk=user.pk).exists():
            username = f'{base}{i}'
            i += 1
        user.username = username
        user.save(update_fields=['username'])
 
    # 4. Criar ou actualizar perfil Utilizador
    try:
        utilizador = user.utilizador
        # marcar como verificado se ainda não estava
        # if not utilizador.verificado:
        #     utilizador.verificado = True
        #     utilizador.save(update_fields=['verificado'])
    except Utilizador.DoesNotExist:
        utilizador = Utilizador.objects.create(
            user=user,
            verificado=False,
        )
        # Download da foto do Google
        if foto_url:
            try:
                import urllib.request
                from django.core.files.base import ContentFile
                img_data = urllib.request.urlopen(foto_url).read()
                utilizador.foto.save(f'google_{google_id}.jpg', ContentFile(img_data), save=True)
            except Exception:
                pass
 
    # 5. Devolver JWT + dados do utilizador (mesmo formato do login normal)
    return Response({
        **_build_auth_response(utilizador, request),
        'criado': criado,
    })