from rest_framework import serializers
from ..models import Loja, UtilizadorLoja
from .UtilizadorSerializer import UtilizadorMiniSerializer


# ══════════════════════════════════════════════════════════════
# STAFF DA LOJA
# ══════════════════════════════════════════════════════════════

class UtilizadorLojaSerializer(serializers.ModelSerializer):
    utilizador    = UtilizadorMiniSerializer(read_only=True)
    utilizador_id = serializers.IntegerField(write_only=True)

    class Meta:
        model  = UtilizadorLoja
        fields = [
            'id', 'utilizador', 'utilizador_id',
            'role', 'ativo', 'data_entrada',
        ]
        read_only_fields = ['data_entrada']

    def validate_utilizador_id(self, value):
        from ..models import Utilizador
        if not Utilizador.objects.filter(id=value, status='ativo').exists():
            raise serializers.ValidationError('Utilizador não encontrado ou inactivo.')
        return value

    def create(self, validated_data):
        from ..models import Utilizador
        utilizador_id = validated_data.pop('utilizador_id')
        utilizador    = Utilizador.objects.get(id=utilizador_id)
        return UtilizadorLoja.objects.create(utilizador=utilizador, **validated_data)


# ══════════════════════════════════════════════════════════════
# LOJA — SERIALIZER COMPLETO  (backoffice)
# ══════════════════════════════════════════════════════════════

class LojaSerializer(serializers.ModelSerializer):

    # ── Leitura ───────────────────────────────────────────────
    dono           = UtilizadorMiniSerializer(read_only=True)
    logo_url       = serializers.SerializerMethodField()
    banner_url     = serializers.SerializerMethodField()
    total_produtos = serializers.SerializerMethodField()
    minha_role     = serializers.SerializerMethodField()

    class Meta:
        model  = Loja
        fields = [
            'id',
            'dono',
            'nome', 'descricao', 'categoria', 'localizacao',
            'percentagem_iva',
            'entrega_ativa', 'levantamento_ativo',
            'logo', 'logo_url',
            'banner', 'banner_url',
            'cor_primaria', 'cor_secundaria',
            'template_id', 'dark_mode',
            'layout_produtos',
            'total_produtos',
            'minha_role',
            'ativa',
            'data_criacao', 'data_atualizacao',
            'politica_devolucao', 'termos_servico', 'politica_privacidade',
            'flutterwave_subaccount_id', 'aceita_flutterwave',
        ]
        read_only_fields = ['dono', 'data_criacao', 'data_atualizacao']
        extra_kwargs = {
            'logo'  : {'write_only': True, 'required': False},
            'banner': {'write_only': True, 'required': False},
        }

    def get_logo_url(self, obj):
        request = self.context.get('request')
        if obj.logo and request:
            return request.build_absolute_uri(obj.logo.url)
        return None

    def get_banner_url(self, obj):
        request = self.context.get('request')
        if obj.banner and request:
            return request.build_absolute_uri(obj.banner.url)
        return None

    def get_total_produtos(self, obj):
        return obj.produtos.filter(ativo=True).count()

    def get_minha_role(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        try:
            membro = UtilizadorLoja.objects.get(
                loja=obj,
                utilizador=request.user.utilizador,
                ativo=True
            )
            return membro.role
        except UtilizadorLoja.DoesNotExist:
            return None

    def create(self, validated_data):
        return Loja.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# ══════════════════════════════════════════════════════════════
# LOJA — SERIALIZER PÚBLICO  (página pública da loja)
# ══════════════════════════════════════════════════════════════

class LojaPublicSerializer(serializers.ModelSerializer):
    logo_url       = serializers.SerializerMethodField()
    banner_url     = serializers.SerializerMethodField()
    rating_medio   = serializers.SerializerMethodField()
    total_avaliacoes = serializers.SerializerMethodField()

    class Meta:
        model  = Loja
        fields = [
            'id', 'nome', 'descricao', 'categoria', 'localizacao',
            'logo_url', 'banner_url',
            'cor_primaria', 'cor_secundaria',
            'template_id', 'dark_mode',
            'layout_produtos',
            'entrega_ativa', 'levantamento_ativo',
            'rating_medio', 'total_avaliacoes',
            'politica_devolucao', 'termos_servico', 'politica_privacidade',
        ]

    def get_logo_url(self, obj):
        request = self.context.get('request')
        if obj.logo and request:
            return request.build_absolute_uri(obj.logo.url)
        return None

    def get_banner_url(self, obj):
        request = self.context.get('request')
        if obj.banner and request:
            return request.build_absolute_uri(obj.banner.url)
        return None

    def get_rating_medio(self, obj):
        avaliacoes = obj.avaliacoes.all()
        if not avaliacoes.exists():
            return None
        total = sum(a.pontuacao for a in avaliacoes)
        return round(total / avaliacoes.count(), 2)

    def get_total_avaliacoes(self, obj):
        return obj.avaliacoes.count()


# ══════════════════════════════════════════════════════════════
# LOJA — SERIALIZER MINI  (usado em listagens, produtos, etc.)
# ══════════════════════════════════════════════════════════════

class LojaMiniSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model  = Loja
        fields = ['id', 'nome', 'categoria', 'logo_url']

    def get_logo_url(self, obj):
        request = self.context.get('request')
        if obj.logo and request:
            return request.build_absolute_uri(obj.logo.url)
        return None