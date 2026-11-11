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
    # o NIF pode vir com espaços ("123 456 789"): limpa-se em validate_nif antes de contar os 9 dígitos
    nif             = serializers.CharField(required=False, allow_blank=True, max_length=20)

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
            'pais', 'concelho', 'cidade', 'codigo_postal',
            'nif', 'nome_fiscal', 'morada_fiscal',
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
        value = value.strip()
        from ..utils.confirmar_email import descartavel, MSG_DESCARTAVEL
        mesmo = self.instance is not None and value.lower() == (self.instance.user.email or '').lower()
        if not mesmo and descartavel(value):
            raise serializers.ValidationError(MSG_DESCARTAVEL)
        return value

    def validate_nif(self, value):
        from ..utils.fiscal import limpar_nif, nif_valido, MSG_NIF
        nif = limpar_nif(value)
        if not nif_valido(nif):
            raise serializers.ValidationError(MSG_NIF)
        return nif

    # ── onde fica a morada (utils/geografia.py) ──
    def validate_pais(self, value):
        from ..utils import geografia
        value = (value or '').strip().upper() or 'CV'
        if not geografia.pais(value):
            raise serializers.ValidationError('País inválido.')
        return value

    def validate_concelho(self, value):
        from ..utils import geografia
        value = (value or '').strip().upper()
        if value and not geografia.concelho(value):
            raise serializers.ValidationError('Concelho inválido.')
        return value

    def validate_cidade(self, value):
        return ' '.join((value or '').split())[:60]

    def validate_codigo_postal(self, value):
        import re
        value = ' '.join((value or '').split())
        if value and not re.fullmatch(r'[A-Za-z0-9 -]{2,16}', value):
            raise serializers.ValidationError('Código postal inválido (letras, números, espaço e hífen).')
        return value

    def validate(self, attrs):
        # fora de Cabo Verde não há concelho; em Cabo Verde a cidade é opcional (o concelho chega)
        pais = attrs.get('pais', getattr(self.instance, 'pais', 'CV') if self.instance else 'CV')
        if pais != 'CV' and ('pais' in attrs or 'concelho' in attrs):
            attrs['concelho'] = ''
        return attrs

    def validate_nome_fiscal(self, value):
        return (value or '').strip()[:200]

    def validate_morada_fiscal(self, value):
        return (value or '').strip()[:300]

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
            if new_email.lower() != (django_user.email or '').lower():
                # email novo: volta a ter de ser confirmado (utils/confirmar_email.py — a view envia o link)
                instance.email_confirmado, instance.email_confirmado_em = False, None
                self.email_mudou = True
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
