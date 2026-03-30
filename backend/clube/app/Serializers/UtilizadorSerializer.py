from rest_framework import serializers
from django.contrib.auth.models import User
from django.db import transaction
from ..models import Utilizador


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
    password        = serializers.CharField(write_only=True, min_length=4, required=False)
    new_username    = serializers.CharField(write_only=True, required=False)
    new_email       = serializers.EmailField(write_only=True, required=False)
    new_first_name  = serializers.CharField(write_only=True, required=False)
    new_last_name   = serializers.CharField(write_only=True, required=False)

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
            'data_criacao', 'data_atualizacao', 'status',
        ]
        read_only_fields = ['verificado', 'rating', 'data_criacao', 'data_atualizacao']

    def get_foto_url(self, obj):
        request = self.context.get('request')
        if obj.foto and request:
            return request.build_absolute_uri(obj.foto.url)
        return None

    # ── CREATE ────────────────────────────────────────────────
    @transaction.atomic
    def create(self, validated_data):
        username   = validated_data.pop('new_username')
        email      = validated_data.pop('new_email')
        password   = validated_data.pop('password')
        first_name = validated_data.pop('new_first_name', '')
        last_name  = validated_data.pop('new_last_name', '')

        # validações de unicidade
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({'username': 'Este username já está em uso.'})
        if User.objects.filter(email=email).exists():
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
            if User.objects.exclude(pk=django_user.pk).filter(username=new_username).exists():
                raise serializers.ValidationError({'username': 'Este username já está em uso.'})
            django_user.username = new_username

        if 'new_email' in validated_data:
            new_email = validated_data.pop('new_email')
            if User.objects.exclude(pk=django_user.pk).filter(email=new_email).exists():
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
    username = serializers.CharField(source='user.username', read_only=True)
    email    = serializers.CharField(source='user.email',    read_only=True)
    nome     = serializers.CharField(read_only=True)   # @property do modelo
    foto_url = serializers.SerializerMethodField()

    class Meta:
        model  = Utilizador
        fields = ['id', 'username', 'nome', 'email', 'foto_url']

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
 
