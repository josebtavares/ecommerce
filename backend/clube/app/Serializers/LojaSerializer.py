from rest_framework import serializers
from ..models import Loja, LojaTemplate, UtilizadorLoja
from .UtilizadorSerializer import UtilizadorMiniSerializer


# ══════════════════════════════════════════════════════════════
# TEMPLATE DE LOJA
# ══════════════════════════════════════════════════════════════

class LojaTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = LojaTemplate
        fields = [
            'id', 'nome', 'tipo_layout', 'imagem_preview',
            'suporta_banner', 'suporta_produtos_destaque',
            'suporta_sidebar', 'ativo',
        ]


# ══════════════════════════════════════════════════════════════
# STAFF DA LOJA
# ══════════════════════════════════════════════════════════════

class UtilizadorLojaSerializer(serializers.ModelSerializer):
    utilizador = UtilizadorMiniSerializer(read_only=True)
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
    dono            = UtilizadorMiniSerializer(read_only=True)
    template        = LojaTemplateSerializer(read_only=True)
    logo_url        = serializers.SerializerMethodField()
    banner_url      = serializers.SerializerMethodField()
    total_produtos  = serializers.SerializerMethodField()
    minha_role      = serializers.SerializerMethodField()

    # ── Escrita ───────────────────────────────────────────────
    template_id     = serializers.PrimaryKeyRelatedField(
                        queryset=LojaTemplate.objects.filter(ativo=True),
                        source='template',
                        write_only=True,
                        required=False,
                        allow_null=True,
                      )

    class Meta:
        model  = Loja
        fields = [
            'id',
            # dono
            'dono',
            # template
            'template', 'template_id',
            # info base
            'nome', 'descricao', 'categoria', 'localizacao',
            'percentagem_iva',
            # entrega
            'entrega_ativa', 'levantamento_ativo',
            # branding
            'logo', 'logo_url',
            'banner', 'banner_url',
            'cor_primaria', 'cor_secundaria',
            'layout_produtos',
            # stats
            'total_produtos',
            # role do utilizador autenticado nesta loja
            'minha_role',
            # estado
            'ativa',
            'data_criacao', 'data_atualizacao',
            'politica_devolucao', 'termos_servico', 'politica_privacidade',
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
        """
        Devolve a role do utilizador autenticado nesta loja.
        Útil para o frontend saber o que mostrar no backoffice.
        """
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
        # dono é injectado pela view via serializer.save(dono=utilizador)
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
    logo_url   = serializers.SerializerMethodField()
    banner_url = serializers.SerializerMethodField()
    template   = LojaTemplateSerializer(read_only=True)
    rating_medio = serializers.SerializerMethodField()

    class Meta:
        model  = Loja
        fields = [
            'id', 'nome', 'descricao', 'categoria', 'localizacao',
            'logo_url', 'banner_url', 'template',
            'cor_primaria', 'cor_secundaria', 'layout_produtos',
            'entrega_ativa', 'levantamento_ativo',
            'rating_medio',
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