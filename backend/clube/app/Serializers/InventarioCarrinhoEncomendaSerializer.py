from rest_framework import serializers
from ..models import Inventario, Carrinho, ItemCarrinho, Encomenda, ItemEncomenda, Produto, Comissao

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
    itens              = ItemEncomendaSerializer(many=True, read_only=True)
    loja_nome          = serializers.CharField(source='loja.nome', read_only=True)
    comprador_username = serializers.CharField(source='comprador.user.username', read_only=True)
    metodo_pagamento   = serializers.SerializerMethodField()
    pagamento_status   = serializers.SerializerMethodField()
    comissao_valor     = serializers.SerializerMethodField()
    comissao_percentagem = serializers.SerializerMethodField()
    receita_liquida    = serializers.SerializerMethodField()
    opcao_entrega_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    entrega_condutor = serializers.SerializerMethodField()
    entrega_status   = serializers.SerializerMethodField()
    comprador_nome     = serializers.CharField(source='comprador.user.get_full_name', read_only=True)
    comprador_email    = serializers.CharField(source='comprador.user.email', read_only=True)
    comprador_telefone = serializers.CharField(source='comprador.telefone', read_only=True)
 
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
            'metodo_pagamento',
            'pagamento_status',
            'comissao_valor',
            'comissao_percentagem',
            'receita_liquida',
            'morada_entrega',
            'notas',
            'data_criacao', 'data_atualizacao',
            'opcao_entrega_id',
            'entrega_condutor', 
            'entrega_status',
            'comprador_nome', 'comprador_email', 'comprador_telefone',
        ]
        read_only_fields = [
            'comprador', 'loja', 'valor_total',
            'data_criacao', 'data_atualizacao',
        ]
 
    def get_metodo_pagamento(self, obj):
        try:
            return obj.pagamento.metodo.tipo if obj.pagamento and obj.pagamento.metodo else None
        except Exception:
            return None
 
    def get_pagamento_status(self, obj):
        try:
            return obj.pagamento.status
        except Exception:
            return None
 
    def get_comissao_valor(self, obj):
        try:
            return str(obj.comissao.valor_comissao)
        except Exception:
            return None
 
    def get_comissao_percentagem(self, obj):
        try:
            return str(obj.comissao.percentagem)
        except Exception:
            return None
 
    def get_receita_liquida(self, obj):
        try:
            return str(obj.valor_total - obj.comissao.valor_comissao)
        except Exception:
            return str(obj.valor_total)
 
    def validate_tipo_entrega(self, value):
        loja = self.context.get('loja')
        if not loja:
            return value
        if value == 'entrega' and not loja.entrega_ativa:
            raise serializers.ValidationError('Esta loja nao oferece entrega ao domicilio.')
        if value == 'levantamento' and not loja.levantamento_ativo:
            raise serializers.ValidationError('Esta loja nao oferece levantamento em loja.')
        return value
 
    def validate(self, attrs):
        if attrs.get('tipo_entrega') == 'entrega':
            if not attrs.get('morada_entrega', '').strip():
                raise serializers.ValidationError(
                    {'morada_entrega': 'Morada de entrega obrigatoria para entregas ao domicilio.'}
                )
        return attrs
    
    def get_entrega_condutor(self, obj):
        try:
            condutor = obj.entrega.condutor
            if not condutor:
                return None
            return condutor.utilizador.nome or condutor.utilizador.username
        except Exception:
            return None
 
    def get_entrega_status(self, obj):
        try:
            return obj.entrega.status
        except Exception:
            return None
        
    def get_comprador_nome(self, obj):
        try:
            return obj.comprador.user.get_full_name() or obj.comprador.user.username
        except Exception:
            return None


class EncomendaMiniSerializer(serializers.ModelSerializer):
    """Usado em listagens — sem itens detalhados."""
    loja_nome          = serializers.CharField(source='loja.nome', read_only=True)
    comprador_username = serializers.CharField(source='comprador.user.username', read_only=True)
    metodo_pagamento   = serializers.SerializerMethodField()
    comissao_valor     = serializers.SerializerMethodField()
    comissao_percentagem = serializers.SerializerMethodField()
    receita_liquida    = serializers.SerializerMethodField()
    comprador_nome     = serializers.CharField(source='comprador.user.get_full_name', read_only=True)
    comprador_email    = serializers.CharField(source='comprador.user.email', read_only=True)
    comprador_telefone = serializers.CharField(source='comprador.telefone', read_only=True)
 
    class Meta:
        model  = Encomenda
        fields = [
            'id', 'loja', 'loja_nome',
            'comprador_username',
            'valor_total',
            'tipo_entrega',
            'status',
            'metodo_pagamento',
            'comissao_valor',
            'comissao_percentagem',
            'receita_liquida',
            'data_criacao',
            'comprador_nome', 'comprador_email', 'comprador_telefone',
        ]
 
    def get_metodo_pagamento(self, obj):
        try:
            return obj.pagamento.metodo.tipo if obj.pagamento and obj.pagamento.metodo else None
        except Exception:
            return None
 
    def get_comissao_valor(self, obj):
        try:
            return str(obj.comissao.valor_comissao)
        except Exception:
            return None
 
    def get_comissao_percentagem(self, obj):
        try:
            return str(obj.comissao.percentagem)
        except Exception:
            return None
 
    def get_receita_liquida(self, obj):
        try:
            return str(obj.valor_total - obj.comissao.valor_comissao)
        except Exception:
            return str(obj.valor_total)
        
    def get_comprador_nome(self, obj):
        try:
            return obj.comprador.user.get_full_name() or obj.comprador.user.username
        except Exception:
            return None


class AtualizarStatusEncomendaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Encomenda
        fields = ['status']
 
    def validate_status(self, value):
        instancia = self.instance
        status_actual = instancia.status
 
        # estados finais — não podem ser alterados
        if status_actual in ('concluido', 'cancelado'):
            raise serializers.ValidationError(
                f'Encomenda já está {status_actual} — não pode ser alterada.'
            )
 
        # ordem válida de progressão (entrega ao domicílio)
        ORDEM_ENTREGA     = ['pendente', 'pago', 'preparando', 'enviado', 'concluido']
        # ordem válida para takeaway — sem "enviado"
        ORDEM_LEVANTAMENTO = ['pendente', 'pago', 'preparando', 'concluido']
 
        # cancelar é sempre permitido
        if value == 'cancelado':
            return value
 
        # takeaway: bloqueia "enviado" e permite preparando → concluido
        if instancia.tipo_entrega == 'levantamento':
            if value == 'enviado':
                raise serializers.ValidationError(
                    'Encomendas de takeaway não podem ser marcadas como "enviado".'
                )
            ordem = ORDEM_LEVANTAMENTO
        else:
            ordem = ORDEM_ENTREGA
 
        idx_actual = ordem.index(status_actual) if status_actual in ordem else -1
        idx_novo   = ordem.index(value)         if value in ordem         else -1
 
        # não permite retroceder após enviado (só para entrega)
        if instancia.tipo_entrega == 'entrega' and status_actual == 'enviado' and idx_novo < idx_actual:
            raise serializers.ValidationError(
                'Não é possível retroceder uma encomenda já enviada.'
            )
 
        return value