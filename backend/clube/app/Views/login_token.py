from rest_framework.exceptions import Throttled, AuthenticationFailed
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from ..autenticacao import conta_ativa
from ..utils.auth import autenticar


class MyTokenSerializer(TokenObtainPairSerializer):
    """
    POST /api/token/ — login JWT alternativo (o site usa /app/utilizador/login/).
    - aceita login por username ou email
    - passa pelo django-axes (utils/auth.autenticar): antes comparava a password à mão
      e as falhas nunca contavam → tentativas ilimitadas de adivinhar a password
    - recusa contas banidas/suspensas
    """

    def validate(self, attrs):
        request = self.context.get('request')
        user, erro, codigo = autenticar(request, attrs.get('username', ''), attrs.get('password', ''))
        if erro:
            if codigo == 429:
                raise Throttled(detail=erro)
            raise AuthenticationFailed(erro)
        if not conta_ativa(user):
            from ..utils.moderacao import mensagem_bloqueio
            perfil = getattr(user, 'utilizador', None)
            raise AuthenticationFailed(mensagem_bloqueio(perfil) if perfil else 'Conta desactivada.')
        try:
            utilizador = user.utilizador
        except Exception:
            raise AuthenticationFailed('Perfil não encontrado.')
        from ..utils.eliminacao import cancelar_ao_entrar
        cancelar_ao_entrar(utilizador)      # pediu para apagar a conta e voltou dentro do prazo

        refresh = self.get_token(user)
        foto_url = utilizador.foto.url if utilizador.foto else None
        return {
            'access_token' : str(refresh.access_token),
            'refresh_token': str(refresh),
            # alinhado com o payload que o frontend guarda em localStorage
            'user': {
                'id'          : utilizador.id,
                'username'    : user.username,
                'email'       : user.email,
                'first_name'  : user.first_name,
                'last_name'   : user.last_name,
                'telefone'    : utilizador.telefone,
                'morada'      : utilizador.morada,
                'foto'        : foto_url,
                'verificado'  : utilizador.verificado,
                'rating'      : str(utilizador.rating),
                'status'      : utilizador.status,
                'data_criacao': utilizador.data_criacao.strftime('%d-%m-%Y %H:%M:%S'),
            },
        }

    @classmethod
    def get_token(cls, user):
        """Adiciona claims personalizadas ao JWT."""
        token = super().get_token(user)
        token['username'] = user.username
        token['is_staff'] = user.is_staff
        return token


class MyTokenView(TokenObtainPairView):
    serializer_class = MyTokenSerializer
    authentication_classes = []   # um token antigo/inválido no browser não pode impedir o login
