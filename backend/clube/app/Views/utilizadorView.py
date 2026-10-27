from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

import logging
import re
from urllib.parse import urlencode

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes, authentication_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from ..models import Utilizador, UtilizadorLoja
from ..utils.auth import autenticar
from ..autenticacao import terminar_sessoes, tokens_depois_da_troca
from ..utils.google_auth import GOOGLE_CLIENT_ID, GOOGLE_REDIRECT_URI, google_obter_utilizador
from ..utils.contas import USERNAME_RE, username_em_uso, email_em_uso, sugerir_usernames
from django_ratelimit.core import is_ratelimited
from ..Serializers.UtilizadorSerializer import (
    UtilizadorSerializer,
    UtilizadorPublicSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)

token_generator = PasswordResetTokenGenerator()


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def _build_user_payload(utilizador: Utilizador, request=None) -> dict:
    """
    Payload do utilizador devolvido no login e no registo.
    Alinhado com o que o frontend guarda em localStorage('user').
    """
    # sem foto → avatar por defeito do storage configurado (media/ na dev, R2 na prod)
    foto_url = utilizador.foto.url if utilizador.foto else default_storage.url('utilizadores/default.png')
    if request:
        foto_url = request.build_absolute_uri(foto_url)

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
        # contas criadas com Google não têm password — o perfil não pede a actual para a definir
        'tem_password'   : utilizador.user.has_usable_password(),
        'is_staff'       : utilizador.user.is_staff,
        'role_admin'     : utilizador.role_admin,           
        'data_criacao'   : utilizador.data_criacao.strftime('%d-%m-%Y %H:%M:%S'),
    }


def _gere_utilizadores(request, superadmin=False) -> bool:
    """Admin da plataforma com gerir_utilizadores (ou só o superadmin). Antes bastava is_staff:
    um moderador ou contabilista via os dados de todos e podia apagar contas."""
    util = getattr(request.user, 'utilizador', None)
    if not util or not util.pode_admin('gerir_utilizadores'):
        return False
    return not superadmin or util.role_admin == 'superadmin'


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
@authentication_classes([])   # um token antigo/inválido no browser não pode impedir o login
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

    # username ou email, numa só tentativa (ver utils/auth.py)
    user, erro, codigo = autenticar(request, username, password)
    if erro:
        return Response({'detail': erro}, status=codigo)

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
    # sem limite um script criava contas em massa (o axes ignora esta rota)
    if is_ratelimited(request=request, group='utilizador_registar', key='ip', rate='10/h', method='POST', increment=True):
        return Response({'detail': 'Demasiados registos a partir desta ligação. Tenta mais tarde.'},
                        status=status.HTTP_429_TOO_MANY_REQUESTS)

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

    # mudar a password ou o email exige a actual (um token roubado não chega para tomar a conta —
    # com o email trocado bastava depois pedir a recuperação da password);
    # quem entrou só com Google ainda não tem password e pode defini-la directamente
    email_novo = (request.data.get('email') or '').strip()
    muda_email = bool(email_novo) and email_novo.lower() != (request.user.email or '').lower()
    if (request.data.get('password') or muda_email) and request.user.has_usable_password():
        if not request.user.check_password(request.data.get('password_atual') or ''):
            return Response(
                {'password_atual': ['A password actual está incorrecta.']},
                status=status.HTTP_400_BAD_REQUEST
            )

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
    payload = _build_user_payload(utilizador, request)
    if data.get('password'):
        # as outras sessões (outros browsers, um token roubado) terminam; esta continua com tokens novos
        access, refresh = tokens_depois_da_troca(request.user, terminar_sessoes(request.user))
        payload.update(access_token=access, refresh_token=refresh)
    return Response(payload, status=status.HTTP_200_OK)


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
    if not _gere_utilizadores(request):
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
    if not _gere_utilizadores(request):
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
    Apenas o superadmin apaga utilizadores (e nunca a própria conta).
    """
    if not _gere_utilizadores(request, superadmin=True):
        return Response({'detail': 'Sem permissão.'}, status=status.HTTP_403_FORBIDDEN)

    from django.db import transaction
    from django.db.models import ProtectedError, RestrictedError

    utilizador = get_object_or_404(Utilizador, id=id)
    if utilizador.user_id == request.user.id:
        return Response({'detail': 'Não podes eliminar a tua própria conta aqui.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        with transaction.atomic():
            utilizador.user.delete()  # cascade apaga o Utilizador também
    except (ProtectedError, RestrictedError) as e:
        # RestrictedError: produto usado num menu de outro POS (ComponenteConjuntoPOS)
        # encomendas, pagamentos, comissões, vendas e turnos POS (on_delete=PROTECT) nunca são
        # apagados — um utilizador com esse histórico deve ser banido/suspenso, não eliminado
        return Response({
            'detail': 'Este utilizador tem registos financeiros (encomendas, vendas POS…) e não pode '
                      'ser eliminado. Bane ou suspende a conta em vez disso.',
            'razoes': sorted({str(o._meta.verbose_name) for o in getattr(e, 'protected_objects', None) or e.restricted_objects}),
        }, status=status.HTTP_409_CONFLICT)
    return Response({'detail': 'Utilizador eliminado.'}, status=status.HTTP_200_OK)


# ══════════════════════════════════════════════════════════════
# PASSWORD RESET
# ══════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    """
    POST /app/utilizador/recuperar_senha/
    Body: { email, destino? }  — destino 'pos' quando o pedido vem do login do POS.
    Envia email com link de recuperação.
    """
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data['email']

    # sem limite dava para encher a caixa de correio de alguém com emails de recuperação
    if (is_ratelimited(request=request, group='recuperar_senha_ip', key='ip', rate='10/h', method='POST', increment=True)
            or is_ratelimited(request=request, group='recuperar_senha_email', key=lambda g, r: email.lower(),
                              rate='3/h', method='POST', increment=True)):
        return Response({'detail': 'Demasiados pedidos. Tenta novamente mais tarde.'},
                        status=status.HTTP_429_TOO_MANY_REQUESTS)

    # .get() rebentava (500) quando dois Users partilham o email
    django_user = User.objects.filter(email__iexact=email, is_active=True).order_by('id').first()
    if not django_user:
        # não revela se o email existe ou não
        return Response(status=status.HTTP_200_OK)

    uid   = urlsafe_base64_encode(force_bytes(django_user.pk))
    token = token_generator.make_token(django_user)

    # pedido feito no login do POS (conta principal) → o link volta à página do POS
    pagina = '/pos/recuperar_senha' if request.data.get('destino') == 'pos' else '/recuperar_senha'
    reset_link = (
        f"{settings.FRONTEND_BASE_URL}{pagina}"
        f"?uid={uid}&token={token}"
    )

    # uma falha do envio fica no log (Sentry) mas a resposta é a mesma: não revela se o email existe
    try:
        send_mail(
            subject='Recuperação de palavra-passe',
            message=(
                f'Olá {django_user.username},\n\n'
                f'Recebemos um pedido para redefinir a password da tua conta Bende.\n'
                f'Abre este link para escolheres uma password nova:\n\n{reset_link}\n\n'
                f'O link só pode ser usado uma vez. Se não foste tu a pedir, ignora este email: '
                f'a tua password não muda.\n\nBende'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[django_user.email],
        )
    except Exception:
        logging.getLogger(__name__).exception('recuperar senha: falhou o envio do email')

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
    terminar_sessoes(django_user)       # quem estava dentro com a password antiga sai

    return Response({'detail': 'Palavra-passe actualizada com sucesso.'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def utilizador_search(request):
    """
    GET /app/utilizador/search/?q=joao&offset=0&limit=20
    """
    # serve para adicionar staff: só quem gere uma loja (dono/gestor) ou o admin da plataforma.
    # Antes qualquer conta listava todos os utilizadores com o email completo.
    if not (request.user.is_staff or UtilizadorLoja.objects.filter(
            utilizador__user=request.user, role__in=('dono', 'gestor'), ativo=True).exists()):
        return Response({'detail': 'Sem permissão.'}, status=status.HTTP_403_FORBIDDEN)

    q = request.query_params.get('q', '').strip()

    try:
        offset = max(int(request.query_params.get('offset', 0)), 0)
        limit = min(int(request.query_params.get('limit', 20)), 50)
    except ValueError:
        return Response({'detail': 'offset/limit inválidos.'}, status=400)

    # sem pesquisa não se lista ninguém (não dá para percorrer a base de utilizadores)
    if len(q) < 3:
        return Response({'count': 0, 'next_offset': None, 'results': []})

    qs = Utilizador.objects.select_related('user').filter(status='ativo')
    # o email só encontra alguém se for escrito completo — não se adivinham emails por partes
    qs = qs.filter(
        Q(user__username__icontains=q) |
        Q(user__email__iexact=q) |
        Q(user__first_name__icontains=q) |
        Q(user__last_name__icontains=q)
    )

    qs = qs.exclude(user=request.user)

    total = qs.count()
    results = qs[offset:offset + limit]

    return Response({
        'count': total,
        'next_offset': offset + limit if offset + limit < total else None,
        'results': [
            {
                'id': u.id,
                'username': u.user.username,
                'nome': u.nome,
                # mascarado, a não ser que tenha sido pesquisado pelo email completo
                'email': u.user.email if u.user.email.lower() == q.lower() else _mascarar_email(u.user.email),
            }
            for u in results
        ]
    })


def _mascarar_email(email):
    """ana.silva@gmail.com → an•••@gmail.com"""
    if not email or '@' not in email:
        return ''
    nome, dominio = email.split('@', 1)
    return f'{nome[:2]}•••@{dominio}'


@api_view(['GET'])
@authentication_classes([])   # um token antigo/inválido no browser não pode impedir o login
@permission_classes([AllowAny])
def google_login_url(request):
    """
    GET /app/utilizador/google/?state=...
    Devolve o URL de autenticação do Google para o frontend redirecionar.
    O `state` é gerado pelo frontend (destino + valor aleatório) e volta intacto no callback:
    protege contra CSRF no login e diz se o login era para a Bendi ou para o POS.
    """
    params = {
        'client_id':     GOOGLE_CLIENT_ID,
        'redirect_uri':  GOOGLE_REDIRECT_URI,
        'response_type': 'code',
        'scope':         'openid email profile',
        'prompt':        'select_account',
    }
    state = request.query_params.get('state', '')
    if re.fullmatch(r'[\w.-]{1,128}', state):
        params['state'] = state
    url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode(params)
    return Response({'url': url})


@api_view(['POST'])
@authentication_classes([])   # um token antigo/inválido no browser não pode impedir o login
@permission_classes([AllowAny])
def google_callback(request):
    """
    POST /app/utilizador/google/callback/
    Body: { code: "..." }
    Recebe o código do Google, cria a conta se não existir e devolve JWT.
    `criado` = conta nova → o frontend pede para completar o perfil.
    """
    utilizador, criado, erro = google_obter_utilizador(request.data.get('code'))
    if erro:
        return erro

    # mesmo formato do login normal
    return Response({
        **_build_auth_response(utilizador, request),
        'criado': criado,
    })


@api_view(['GET'])
@authentication_classes([])   # público (registo); no perfil o frontend não verifica o próprio valor
@permission_classes([AllowAny])
def utilizador_disponivel(request):
    """
    GET /app/utilizador/disponivel/?username=…&email=…  (os dois são opcionais)
    Verificação ao vivo nos formulários (registo, staff, perfil, POS):
    { username: {disponivel, motivo?, sugestoes?}, email: {disponivel, motivo?} }
    O servidor volta a validar tudo ao gravar — isto é só para avisar mais cedo.
    """
    # o registo já diz se um email existe; o limite trava a enumeração em massa
    if is_ratelimited(request=request, group='utilizador_disponivel', key='ip',
                      rate='60/m', method='GET', increment=True):
        return Response({'detail': 'Demasiados pedidos. Aguarda um momento.'},
                        status=status.HTTP_429_TOO_MANY_REQUESTS)

    resposta = {}

    username = (request.query_params.get('username') or '').strip()
    if username:
        if not USERNAME_RE.match(username):
            resposta['username'] = {
                'disponivel': False,
                'motivo': 'Só letras, números e @ . + - _ (3 a 150 caracteres).',
            }
        elif username_em_uso(username):
            resposta['username'] = {
                'disponivel': False,
                'motivo': 'Este username já está em uso.',
                'sugestoes': sugerir_usernames(username),
            }
        else:
            resposta['username'] = {'disponivel': True}

    email = (request.query_params.get('email') or '').strip()
    if email:
        if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
            resposta['email'] = {'disponivel': False, 'motivo': 'Email inválido.'}
        elif email_em_uso(email):
            resposta['email'] = {'disponivel': False, 'motivo': 'Este email já está registado.'}
        else:
            resposta['email'] = {'disponivel': True}

    return Response(resposta)
