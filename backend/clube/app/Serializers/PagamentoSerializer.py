from rest_framework import serializers
from ..models import Pagamento, MetodoPagamento, CartaoGuardado, Encomenda


# ══════════════════════════════════════════════════════════════
# CARTÃO GUARDADO
# ══════════════════════════════════════════════════════════════

class CartaoGuardadoSerializer(serializers.ModelSerializer):
    """
    Só expõe dados de display — nunca tokens internos.
    Os tokens Stripe são usados apenas internamente nas views.
    """
    expiracao = serializers.SerializerMethodField()

    class Meta:
        model  = CartaoGuardado
        fields = [
            'id', 'marca', 'ultimos_4',
            'mes_expiracao', 'ano_expiracao', 'expiracao',
            'predefinido', 'data_criacao',
        ]
        read_only_fields = fields

    def get_expiracao(self, obj):
        return f'{obj.mes_expiracao:02d}/{str(obj.ano_expiracao)[-2:]}'


# ══════════════════════════════════════════════════════════════
# MÉTODO DE PAGAMENTO DA LOJA
# ══════════════════════════════════════════════════════════════

class MetodoPagamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = MetodoPagamento
        fields = ['id', 'tipo', 'ativo']


# ══════════════════════════════════════════════════════════════
# PAGAMENTO
# ══════════════════════════════════════════════════════════════

# Substitui PagamentoSerializer no ficheiro PagamentoSerializer.py

class PagamentoSerializer(serializers.ModelSerializer):
    metodo_tipo          = serializers.CharField(source='metodo.tipo', read_only=True, default=None)
    loja_nome            = serializers.SerializerMethodField()
    comprador_username   = serializers.SerializerMethodField()
    comissao_valor       = serializers.SerializerMethodField()
    comissao_percentagem = serializers.SerializerMethodField()
    receita_liquida      = serializers.SerializerMethodField()
    data_criacao         = serializers.DateTimeField(format='%d-%m-%Y %H:%M', read_only=True)

    class Meta:
        model  = Pagamento
        fields = [
            'id',
            'encomenda',
            'metodo',
            'metodo_tipo',
            'loja_nome',
            'comprador_username',
            'valor',
            'status',
            'referencia_transacao',
            'comissao_valor',
            'comissao_percentagem',
            'receita_liquida',
            'data_criacao',
        ]

    def get_loja_nome(self, obj):
        try:
            return obj.encomenda.loja.nome
        except Exception:
            return None

    def get_comprador_username(self, obj):
        try:
            return obj.encomenda.comprador.user.username
        except Exception:
            return None

    def get_comissao_valor(self, obj):
        try:
            return str(obj.encomenda.comissao.valor_comissao)
        except Exception:
            return None

    def get_comissao_percentagem(self, obj):
        try:
            return str(obj.encomenda.comissao.percentagem)
        except Exception:
            return None

    def get_receita_liquida(self, obj):
        try:
            return str(obj.encomenda.valor_total - obj.encomenda.comissao.valor_comissao)
        except Exception:
            return str(obj.valor)


# ══════════════════════════════════════════════════════════════
# PAYLOADS DE INPUT
# ══════════════════════════════════════════════════════════════

class PagarComCartaoSerializer(serializers.Serializer):
    """
    Payload para pagar com cartão Stripe.
    Aceita cartão guardado ou novo cartão via payment_method_id do Stripe.js
    """
    encomenda_id      = serializers.IntegerField()
    # opção A: cartão já guardado
    cartao_id         = serializers.IntegerField(required=False, allow_null=True)
    # opção B: novo cartão via Stripe.js (frontend tokenizou)
    payment_method_id = serializers.CharField(required=False, allow_null=True)
    # guardar o novo cartão para uso futuro?
    guardar_cartao    = serializers.BooleanField(default=False)

    def validate(self, attrs):
        if not attrs.get('cartao_id') and not attrs.get('payment_method_id'):
            raise serializers.ValidationError(
                'Fornece cartao_id (cartão guardado) ou payment_method_id (novo cartão).'
            )
        return attrs


class PagarComMBWaySerializer(serializers.Serializer):
    encomenda_id = serializers.IntegerField()
    telemovel    = serializers.CharField(max_length=20)


class PagarComDinheiroSerializer(serializers.Serializer):
    encomenda_id = serializers.IntegerField()