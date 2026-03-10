from django.contrib.auth.models import User
from django.db.models import Q

from rest_framework import serializers
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class MyTokenSerializer(TokenObtainPairSerializer):
    """
    Serializer JWT customizado:
    - aceita login por username ou email
    - devolve dados do utilizador no payload
    - adiciona claims ao token (username, is_staff)
    """

    def validate(self, attrs):
        username = attrs.get('username', '').strip()
        password = attrs.get('password', '')

        # 1) procurar o Django User por username ou email (case-insensitive)
        django_user = User.objects.filter(
            Q(username__iexact=username) | Q(email__iexact=username)
        ).first()

        if not django_user:
            raise serializers.ValidationError(
                {'detail': 'Credenciais inválidas.'},
                code='authorization'
            )

        # 2) verificar a password via Django (check_password faz a comparação do hash)
        if not django_user.check_password(password):
            raise serializers.ValidationError(
                {'detail': 'Credenciais inválidas.'},
                code='authorization'
            )

        # 3) verificar se o utilizador está activo
        if not django_user.is_active:
            raise serializers.ValidationError(
                {'detail': 'Conta desactivada.'},
                code='authorization'
            )

        # 4) verificar se tem Utilizador ligado
        try:
            utilizador = django_user.utilizador
        except Exception:
            raise serializers.ValidationError(
                {'detail': 'Perfil não encontrado.'},
                code='authorization'
            )

        if not utilizador.is_active:
            raise serializers.ValidationError(
                {'detail': 'Conta desactivada.'},
                code='authorization'
            )

        # 5) forçar o username correcto para o SimpleJWT gerar o token
        attrs['username'] = django_user.username
        data = super().validate(attrs)

        # 6) adicionar dados do utilizador à resposta
        #    — alinhado com o payload que o frontend guarda em localStorage
        foto_url = utilizador.foto.url if utilizador.foto else None

        data['user'] = {
            'id'          : utilizador.id,
            'username'    : django_user.username,
            'email'       : django_user.email,
            'first_name'  : django_user.first_name,
            'last_name'   : django_user.last_name,
            'telefone'    : utilizador.telefone,
            'morada'      : utilizador.morada,
            'foto'        : foto_url,
            'verificado'  : utilizador.verificado,
            'rating'      : str(utilizador.rating),
            'status'      : utilizador.status,
            'data_criacao': utilizador.data_criacao.strftime('%d-%m-%Y %H:%M:%S'),
        }

        # renomear para coincidir com o que o frontend guarda
        data['access_token']  = data.pop('access')
        data['refresh_token'] = data.pop('refresh')

        return data

    @classmethod
    def get_token(cls, user):
        """Adiciona claims personalizadas ao JWT."""
        token = super().get_token(user)
        token['username'] = user.username
        token['is_staff'] = user.is_staff
        return token


class MyTokenView(TokenObtainPairView):
    serializer_class = MyTokenSerializer