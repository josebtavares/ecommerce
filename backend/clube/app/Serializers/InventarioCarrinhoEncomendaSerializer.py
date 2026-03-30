from rest_framework import serializers
from ..models import (
    Inventario, Carrinho, ItemCarrinho,
    Encomenda, ItemEncomenda, Produto
)
from .ProdutoSerializer import ProdutoMiniSerializer
from .LojaSerializer import LojaMiniSerializer


# ══════════════════════════════════════════════════════════════
# INVENTÁRIO
# ══════════════════════════════════════════════════════════════

class InventarioSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    produto_sku  = serializers.CharField(source='produto.sku',  read_only=True)

    class Meta:
        model  = Inventario
        fields = [
            'id',
            'produto', 'produto_nome', 'produto_sku',
            'quantidade',
            'preco_custo', 'preco_venda',
            'data_atualizacao',
        ]
        read_only_fields = ['data_atualizacao']

    def validate_quantidade(self, value):
        if value < 0:
            raise serializers.ValidationError('A quantidade não pode ser negativa.')
        return value

    def validate_preco_custo(self, value):
        if value < 0:
            raise serializers.ValidationError('O preço de custo não pode ser negativo.')
        return value

    def validate_preco_venda(self, value):
        if value < 0:
            raise serializers.ValidationError('O preço de venda não pode ser negativo.')
        return value


# ══════════════════════════════════════════════════════════════
# CARRINHO
# ══════════════════════════════════════════════════════════════

class ItemCarrinhoSerializer(serializers.ModelSerializer):
    produto  = ProdutoMiniSerializer(read_only=True)
    produto_id = serializers.PrimaryKeyRelatedField(
        queryset=Produto.objects.filter(ativo=True),
        source='produto',
        write_only=True,
    )
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model  = ItemCarrinho
        fields = ['id', 'produto', 'produto_id', 'quantidade', 'atributos', 'subtotal']

    def get_subtotal(self, obj):
        return round(float(obj.produto.preco) * obj.quantidade, 2)

    def validate_quantidade(self, value):
        if value < 1:
            raise serializers.ValidationError('A quantidade mínima é 1.')
        return value

    def validate(self, attrs):
        produto    = attrs.get('produto')
        quantidade = attrs.get('quantidade', 1)
        # verifica stock disponível
        try:
            if produto.inventario.quantidade < quantidade:
                raise serializers.ValidationError(
                    {'quantidade': f'Stock insuficiente. Disponível: {produto.inventario.quantidade}'}
                )
        except Inventario.DoesNotExist:
            pass  # sem inventario registado — permite
        return attrs


class CarrinhoSerializer(serializers.ModelSerializer):
    itens       = ItemCarrinhoSerializer(many=True, read_only=True)
    total       = serializers.SerializerMethodField()
    total_itens = serializers.SerializerMethodField()
    loja        = LojaMiniSerializer(read_only=True)

    class Meta:
        model  = Carrinho
        fields = [
            'id', 'loja',
            'itens', 'total', 'total_itens',
            'data_criacao',
        ]
        read_only_fields = ['data_criacao']

    def get_total(self, obj):
        return round(sum(
            float(item.produto.preco) * item.quantidade
            for item in obj.itens.select_related('produto').all()
        ), 2)

    def get_total_itens(self, obj):
        return obj.itens.count()


# ══════════════════════════════════════════════════════════════
# ENCOMENDA
# ══════════════════════════════════════════════════════════════

class ItemEncomendaSerializer(serializers.ModelSerializer):
    produto = ProdutoMiniSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model  = ItemEncomenda
        fields = ['id', 'produto', 'quantidade', 'preco', 'atributos', 'subtotal']

    def get_subtotal(self, obj):
        return round(float(obj.preco) * obj.quantidade, 2)


class EncomendaSerializer(serializers.ModelSerializer):
    itens        = ItemEncomendaSerializer(many=True, read_only=True)
    loja_nome    = serializers.CharField(source='loja.nome',      read_only=True)
    comprador_username = serializers.CharField(
        source='comprador.user.username', read_only=True
    )

    class Meta:
        model  = Encomenda
        fields = [
            'id',
            'comprador', 'comprador_username',
            'loja', 'loja_nome',
            'itens',
            'valor_total',
            'tipo_entrega',
            'status',
            'morada_entrega',
            'notas',
            'data_criacao', 'data_atualizacao',
        ]
        read_only_fields = [
            'comprador', 'loja', 'valor_total',
            'data_criacao', 'data_atualizacao',
        ]

    def validate_tipo_entrega(self, value):
        """Valida se a loja suporta o tipo de entrega escolhido."""
        loja = self.context.get('loja')
        if not loja:
            return value
        if value == 'entrega' and not loja.entrega_ativa:
            raise serializers.ValidationError('Esta loja não oferece entrega ao domicílio.')
        if value == 'levantamento' and not loja.levantamento_ativo:
            raise serializers.ValidationError('Esta loja não oferece levantamento em loja.')
        return value

    def validate(self, attrs):
        if attrs.get('tipo_entrega') == 'entrega':
            if not attrs.get('morada_entrega', '').strip():
                raise serializers.ValidationError(
                    {'morada_entrega': 'Morada de entrega obrigatória para entregas ao domicílio.'}
                )
        return attrs


class EncomendaMiniSerializer(serializers.ModelSerializer):
    """Usado em listagens — sem itens detalhados."""
    loja_nome = serializers.CharField(source='loja.nome', read_only=True)

    class Meta:
        model  = Encomenda
        fields = [
            'id', 'loja', 'loja_nome',
            'valor_total', 'tipo_entrega',
            'status', 'data_criacao',
        ]


class AtualizarStatusEncomendaSerializer(serializers.ModelSerializer):
    """Usado pelo backoffice da loja para mudar o status livremente."""
    class Meta:
        model  = Encomenda
        fields = ['status']
 
    def validate_status(self, value):
        instancia = self.instance
        # só bloqueia estados terminais — o backoffice pode mudar livremente os outros
        if instancia.status in ('concluido', 'cancelado'):
            raise serializers.ValidationError(
                f'Encomenda já está {instancia.status} — não pode ser alterada.'
            )
        return value