from rest_framework import serializers
from django.contrib.auth.models import User
from django.db import transaction
from ..models import Utilizador
from ..utils.password import mensagem_password_fraca
from ..utils.contas import USERNAME_RE, username_em_uso, email_em_uso


# ══════════════════════════════════════════════════════════════
# SERIALIZER PRINCIPAL
# ══════════════════════════════════════════════════════════════

class UtilizadorSerializer(serializers.ModelSerializer):

    # ── Leitura (read-only) — vêm do User do Django ──────────
    username        = serializers.CharField(source='user.username', read_only=True)
    email           = serializers.EmailField(source='user.email', read_only=True)
    first_name      = serializers.CharField(source='user.first_name', read_only=True)
    last_name       = serializers.CharField(source='user.last_name', read_only=True)
    foto_url        = serializers.SerializerMethodField()

    # ── Escrita (write-only) — usados no registo/update ──────
    password        = serializers.CharField(write_only=True, required=False)
    new_username    = serializers.CharField(write_only=True, required=False)
    new_email       = serializers.EmailField(write_only=True, required=False)
    new_first_name  = serializers.CharField(write_only=True, required=False)
    new_last_name   = serializers.CharField(write_only=True, required=False, allow_blank=True)  # o apelido é opcional no registo

    class Meta:
        model  = Utilizador
        fields = [
            # identificação
            'id',
            # do Django User (read-only)
            'username', 'email', 'first_name', 'last_name',
            # escrita
            'new_username', 'new_email', 'new_first_name', 'new_last_name', 'password',
            # do Utilizador
            'telefone', 'morada', 'foto', 'foto_url',
            'verificado', 'rating',
            'role_admin', 
            'data_criacao', 'data_atualizacao', 'status',
        ]
        read_only_fields = ['verificado', 'rating', 'role_admin', 'data_criacao', 'data_atualizacao']

    def get_foto_url(self, obj):
        request = self.context.get('request')
        if obj.foto and request:
            return request.build_absolute_uri(obj.foto.url)
        return None

    def validate_new_username(self, value):
        value = value.strip()
        # um username antigo que não mudou passa sempre (contas criadas antes desta regra)
        if self.instance is not None and value == self.instance.user.username:
            return value
        if not USERNAME_RE.match(value):
            raise serializers.ValidationError(
                'O username só pode ter letras, números e @ . + - _ (3 a 150 caracteres).'
            )
        return value

    def validate_new_email(self, value):
        return value.strip()

    # registo e alteração de password no perfil usam as mesmas regras do staff
    def validate_password(self, value):
        msg = mensagem_password_fraca(value)
        if msg:
            raise serializers.ValidationError(msg)
        return value

    # ── CREATE ────────────────────────────────────────────────
    @transaction.atomic
    def create(self, validated_data):
        username   = validated_data.pop('new_username')
        email      = validated_data.pop('new_email')
        password   = validated_data.pop('password')
        first_name = validated_data.pop('new_first_name', '')
        last_name  = validated_data.pop('new_last_name', '')

        # validações de unicidade
        if username_em_uso(username):
            raise serializers.ValidationError({'username': 'Este username já está em uso.'})
        if email_em_uso(email):
            raise serializers.ValidationError({'email': 'Este email já está em uso.'})

        django_user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        utilizador = Utilizador.objects.create(user=django_user, **validated_data)
        return utilizador

    # ── UPDATE ────────────────────────────────────────────────
    @transaction.atomic
    def update(self, instance, validated_data):
        django_user = instance.user

        # campos do User do Django
        if 'new_username' in validated_data:
            new_username = validated_data.pop('new_username')
            if username_em_uso(new_username, excluir=django_user):
                raise serializers.ValidationError({'username': 'Este username já está em uso.'})
            django_user.username = new_username

        if 'new_email' in validated_data:
            new_email = validated_data.pop('new_email')
            if email_em_uso(new_email, excluir=django_user):
                raise serializers.ValidationError({'email': 'Este email já está em uso.'})
            django_user.email = new_email

        if 'new_first_name' in validated_data:
            django_user.first_name = validated_data.pop('new_first_name')

        if 'new_last_name' in validated_data:
            django_user.last_name = validated_data.pop('new_last_name')

        if 'password' in validated_data:
            django_user.set_password(validated_data.pop('password'))

        django_user.save()

        # campos do Utilizador
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance



class UtilizadorPublicSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    nome     = serializers.CharField(read_only=True)   # @property do modelo
    foto_url = serializers.SerializerMethodField()

    class Meta:
        model  = Utilizador
        fields = ['id', 'username', 'nome', 'foto_url', 'rating', 'verificado']

    def get_foto_url(self, obj):
        request = self.context.get('request')
        if obj.foto and request:
            return request.build_absolute_uri(obj.foto.url)
        return None


class UtilizadorMiniSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    email    = serializers.CharField(source='user.email',    read_only=True)
    nome     = serializers.CharField(read_only=True)   # @property do modelo
    foto_url = serializers.SerializerMethodField()

    class Meta:
        model  = Utilizador
        fields = ['id', 'username', 'nome', 'email', 'foto_url']

    def get_username(self, obj):
        # conta apagada (utils/eliminacao.py): comentários e avaliações ficam, sem o nome
        return 'Utilizador eliminado' if obj.status == 'eliminado' else obj.user.username

    def get_foto_url(self, obj):
        request = self.context.get('request')
        if obj.foto and request:
            return request.build_absolute_uri(obj.foto.url)
        return None



class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid          = serializers.CharField()
    token        = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
 

    def validate_new_password(self, value):
        msg = mensagem_password_fraca(value)
        if msg:
            raise serializers.ValidationError(msg)
        return value
