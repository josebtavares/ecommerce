from rest_framework import serializers
from ..models import Loja, UtilizadorLoja
from .UtilizadorSerializer import UtilizadorMiniSerializer


# ══════════════════════════════════════════════════════════════
# STAFF DA LOJA
# ══════════════════════════════════════════════════════════════

class UtilizadorLojaSerializer(serializers.ModelSerializer):
    utilizador    = UtilizadorMiniSerializer(read_only=True)
    utilizador_id = serializers.IntegerField(write_only=True)
    # chat: pode_chat só conta para staff/contabilista — dono e gestor atendem sempre
    atende_chat   = serializers.BooleanField(read_only=True)

    class Meta:
        model  = UtilizadorLoja
        fields = [
            'id', 'utilizador', 'utilizador_id',
            'role', 'ativo', 'data_entrada', 'pode_chat', 'atende_chat',
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
    banner_poster_url = serializers.SerializerMethodField()
    total_produtos = serializers.SerializerMethodField()
    minha_role     = serializers.SerializerMethodField()
    meu_chat       = serializers.SerializerMethodField()   # 'total' | 'condutor' | None (caixa da loja)

    class Meta:
        model  = Loja
        fields = [
            'id',
            'dono',
            'nome', 'descricao', 'categoria', 'localizacao',
            'percentagem_iva',
            'entrega_ativa', 'levantamento_ativo',
            'logo', 'logo_url',
            'banner', 'banner_url', 'banner_poster_url', 'banner_estado',
            'cor_primaria', 'cor_secundaria',
            'template_id', 'dark_mode',
            'layout_produtos',
            'total_produtos',
            'minha_role', 'meu_chat',
            'ativa', 'estado', 'estado_motivo', 'estado_alterado_em',
            'data_criacao', 'data_atualizacao',
            'politica_devolucao', 'termos_servico', 'politica_privacidade',
            'flutterwave_subaccount_id', 'aceita_flutterwave',
            'modelo_cobranca', 'percentagem_comissao',
        ]
        # estado/ativa só mudam pelos endpoints próprios (fechar/reabrir, admin) — nunca por PATCH;
        # o modelo de cobrança e a comissão só os muda o admin
        read_only_fields = ['dono', 'data_criacao', 'data_atualizacao', 'banner_estado',
                            'ativa', 'estado', 'estado_motivo', 'estado_alterado_em',
                            'modelo_cobranca', 'percentagem_comissao']
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

    def get_banner_poster_url(self, obj):
        request = self.context.get('request')
        if obj.banner_poster and request:
            return request.build_absolute_uri(obj.banner_poster.url)
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

    def get_meu_chat(self, obj):
        """Acesso à caixa de mensagens da loja (o backoffice mostra os "Clientes" no chat)."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        from ..chat.regras import acesso_caixa
        from ..chat.models import Caixa
        caixa = Caixa.objects.filter(tipo=Caixa.LOJA, loja=obj).first() or Caixa(tipo=Caixa.LOJA, loja=obj)
        try:
            return acesso_caixa(request.user.utilizador, caixa)
        except Exception:
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
    banner_poster_url = serializers.SerializerMethodField()
    rating_medio   = serializers.SerializerMethodField()
    total_avaliacoes = serializers.SerializerMethodField()
    horario        = serializers.SerializerMethodField()   # aberta/fechada + semana (utils/horarios.py)
    agendamento    = serializers.SerializerMethodField()   # o cliente pode escolher dia e hora?

    class Meta:
        model  = Loja
        fields = [
            'id', 'nome', 'descricao', 'categoria', 'localizacao',
            'logo_url', 'banner_url', 'banner_poster_url', 'banner_estado',
            'cor_primaria', 'cor_secundaria',
            'template_id', 'dark_mode',
            'layout_produtos',
            'entrega_ativa', 'levantamento_ativo',
            'rating_medio', 'total_avaliacoes',
            'politica_devolucao', 'termos_servico', 'politica_privacidade',
            'horario', 'agendamento',
        ]

    def get_horario(self, obj):
        from ..utils.horarios import payload_publico
        return payload_publico(obj)

    def get_agendamento(self, obj):
        from ..utils.horarios import agendamento_publico
        return agendamento_publico(obj)

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

    def get_banner_poster_url(self, obj):
        request = self.context.get('request')
        if obj.banner_poster and request:
            return request.build_absolute_uri(obj.banner_poster.url)
        return None

    def _visiveis(self, obj):
        # só as avaliações que o público vê (as ocultas pela loja não contam) — percorre .all() para usar o prefetch
        if not hasattr(obj, '_notas_visiveis'):
            obj._notas_visiveis = [a.pontuacao for a in obj.avaliacoes.all() if not a.oculta]
        return obj._notas_visiveis

    def get_rating_medio(self, obj):
        notas = self._visiveis(obj)
        return round(sum(notas) / len(notas), 2) if notas else None

    def get_total_avaliacoes(self, obj):
        return len(self._visiveis(obj))


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