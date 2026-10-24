from rest_framework import serializers
from ..models import Inventario, Carrinho, ItemCarrinho, Encomenda, ItemEncomenda, Produto, Comissao

from .ProdutoSerializer import ProdutoMiniSerializer
from .LojaSerializer import LojaMiniSerializer
from ..utils.variantes import tem_atributos_variante


# ══════════════════════════════════════════════════════════════
# INVENTÁRIO
# ══════════════════════════════════════════════════════════════

class InventarioSerializer(serializers.ModelSerializer):
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    produto_sku  = serializers.CharField(source='produto.sku',  read_only=True)
    stock_por_variante  = serializers.BooleanField(source='produto.stock_por_variante', read_only=True)
    variantes           = serializers.SerializerMethodField()
    variantes_pendentes = serializers.SerializerMethodField()

    class Meta:
        model  = Inventario
        fields = [
            'id',
            'produto', 'produto_nome', 'produto_sku',
            'quantidade',
            'preco_custo', 'preco_venda',
            'stock_por_variante', 'variantes', 'variantes_pendentes',
            'data_atualizacao',
        ]
        read_only_fields = ['data_atualizacao']

    def get_variantes(self, obj):
        """Resumo das variantes activas (para o chip e a lista no Inventário)."""
        if not obj.produto.stock_por_variante:
            return []
        return [
            {'id': v.id, 'chave': v.chave, 'combinacao': v.combinacao, 'quantidade': v.quantidade}
            for v in obj.produto.variantes.all() if v.ativo
        ]

    def get_variantes_pendentes(self, obj):
        return not obj.produto.stock_por_variante and tem_atributos_variante(obj.produto)

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
    subtotal       = serializers.SerializerMethodField()
    preco_unitario = serializers.SerializerMethodField()
    variante       = serializers.SerializerMethodField()
    escolhas_texto = serializers.SerializerMethodField()   # menu: "Bebida: Fanta (33cl) +50$00"

    class Meta:
        model  = ItemCarrinho
        fields = ['id', 'produto', 'produto_id', 'quantidade', 'atributos',
                  'variante', 'preco_unitario', 'subtotal', 'escolhas', 'escolhas_texto']

    def get_escolhas_texto(self, obj):
        if not (obj.escolhas and obj.produto.e_conjunto):
            return ''
        from ..utils.conjuntos import texto_escolhas
        return texto_escolhas(obj.produto, obj.escolhas)

    def get_preco_unitario(self, obj):
        return str(obj.preco_unitario)

    def get_subtotal(self, obj):
        return round(float(obj.preco_unitario) * obj.quantidade, 2)

    def get_variante(self, obj):
        """Variante escolhida + stock actual dela (para avisar se baixou entretanto)."""
        v = obj.variante
        if not v:
            return None
        return {
            'id': v.id, 'combinacao': v.combinacao, 'ativo': v.ativo,
            'quantidade_disponivel': v.quantidade,
        }

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
            float(item.preco_unitario) * item.quantidade
            for item in obj.itens.select_related('produto', 'variante').all()
        ), 2)

    def get_total_itens(self, obj):
        return obj.itens.count()


# ══════════════════════════════════════════════════════════════
# ENCOMENDA
# ══════════════════════════════════════════════════════════════

class ItemEncomendaSerializer(serializers.ModelSerializer):
    produto = ProdutoMiniSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()
    qtd_reembolsada = serializers.SerializerMethodField()   # unidades já reembolsadas (p.ex. esgotadas)

    class Meta:
        model  = ItemEncomenda
        fields = ['id', 'produto', 'quantidade', 'preco', 'atributos', 'variante', 'componentes', 'subtotal',
                  'qtd_reembolsada']

    def get_qtd_reembolsada(self, obj):
        from django.db.models import Sum
        return obj.reembolsos.filter(reembolso__data_reembolso__isnull=False).aggregate(q=Sum('quantidade'))['q'] or 0

    def get_subtotal(self, obj):
        return round(float(obj.preco) * obj.quantidade, 2)


def _reembolso_resumo(obj):
    """O pedido de reembolso mais recente da encomenda (ou None) — para o selo na lista e no detalhe."""
    r = obj.reembolsos.order_by('-id').first()
    if not r:
        return None
    return {'id': r.id, 'estado': r.estado, 'estado_label': r.get_estado_display(), 'tipo': r.tipo, 'motivo': r.motivo,
            'metodo': r.metodo,
            'valor': str(r.valor_aprovado if r.valor_aprovado is not None else r.valor_pedido)}


def _receita_liquida(obj):
    """O que a loja fica: total − reembolsado (incl. esgotados descontados) − comissão (já recalculada)."""
    from django.db.models import Sum
    reemb = obj.reembolsos.filter(data_reembolso__isnull=False).aggregate(t=Sum('valor_aprovado'))['t'] or 0
    try:
        com = obj.comissao.valor_comissao
    except Exception:
        com = 0
    return str(obj.valor_total - reemb - com)


def _fatura(obj, request):
    """Fatura que a loja registou (emitida no e-Fatura) — None enquanto estiver por faturar."""
    if not obj.fatura_registada_em:
        return None
    pdf = None
    if obj.fatura_pdf:
        pdf = request.build_absolute_uri(obj.fatura_pdf.url) if request else obj.fatura_pdf.url
    return {'numero': obj.fatura_numero, 'pdf_url': pdf, 'registada_em': obj.fatura_registada_em}


def _valor_a_pagar(obj):
    try:
        p = obj.pagamento
    except Exception:
        return None
    return str(p.valor) if p.status == 'pendente' else None


def _valor_reembolsado(obj):
    from django.db.models import Sum
    # dinheiro devolvido (os esgotados descontados antes de pagar não contam — vêem-se em valor_a_pagar)
    return str(obj.reembolsos.filter(data_reembolso__isnull=False).exclude(metodo='abatido')
               .aggregate(t=Sum('valor_aprovado'))['t'] or '0.00')


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
    agendada_texto     = serializers.SerializerMethodField()
    reembolso          = serializers.SerializerMethodField()
    valor_reembolsado  = serializers.SerializerMethodField()
    valor_a_pagar      = serializers.SerializerMethodField()   # ainda por cobrar (dinheiro), já sem os esgotados
    fatura             = serializers.SerializerMethodField()   # registada pela loja (utils/fiscal.py)
 
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
            'agendada_para', 'agendada_texto', 'agendamento_origem',
            'comprador_nome', 'comprador_email', 'comprador_telefone',
            'reembolso', 'valor_reembolsado', 'valor_a_pagar',
            'fatura',
        ]
        read_only_fields = [
            'comprador', 'loja', 'valor_total', 'agendada_para', 'agendamento_origem',
            'data_criacao', 'data_atualizacao',
        ]
 
    def get_reembolso(self, obj):
        return _reembolso_resumo(obj)

    def get_valor_reembolsado(self, obj):
        return _valor_reembolsado(obj)

    def get_valor_a_pagar(self, obj):
        return _valor_a_pagar(obj)

    def get_fatura(self, obj):
        return _fatura(obj, self.context.get('request'))

    def get_agendada_texto(self, obj):
        if not obj.agendada_para:
            return ""
        from ..utils.horarios import fuso, DIAS
        d = obj.agendada_para.astimezone(fuso())
        return f"{DIAS[d.weekday()]} {d:%d/%m} às {d:%H:%M}"

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
        return _receita_liquida(obj)
 
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
    pagamento_status   = serializers.SerializerMethodField()   # o backoffice avisa se cancelar reembolsa
    loja_nome          = serializers.CharField(source='loja.nome', read_only=True)
    comprador_username = serializers.CharField(source='comprador.user.username', read_only=True)
    metodo_pagamento   = serializers.SerializerMethodField()
    comissao_valor     = serializers.SerializerMethodField()
    comissao_percentagem = serializers.SerializerMethodField()
    receita_liquida    = serializers.SerializerMethodField()
    comprador_nome     = serializers.CharField(source='comprador.user.get_full_name', read_only=True)
    comprador_email    = serializers.CharField(source='comprador.user.email', read_only=True)
    comprador_telefone = serializers.CharField(source='comprador.telefone', read_only=True)
    agendada_texto     = serializers.SerializerMethodField()
    reembolso          = serializers.SerializerMethodField()
    valor_reembolsado  = serializers.SerializerMethodField()
    valor_a_pagar      = serializers.SerializerMethodField()   # ainda por cobrar (dinheiro), já sem os esgotados
    fatura             = serializers.SerializerMethodField()   # registada pela loja (utils/fiscal.py)
 
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
            'agendada_para', 'agendada_texto', 'agendamento_origem',
            'reembolso', 'valor_reembolsado', 'pagamento_status', 'valor_a_pagar',
            'fatura',
        ]
 
    def get_pagamento_status(self, obj):
        try:
            return obj.pagamento.status
        except Exception:
            return None

    def get_reembolso(self, obj):
        return _reembolso_resumo(obj)

    def get_valor_reembolsado(self, obj):
        return _valor_reembolsado(obj)

    def get_valor_a_pagar(self, obj):
        return _valor_a_pagar(obj)

    def get_fatura(self, obj):
        return _fatura(obj, self.context.get('request'))

    def get_agendada_texto(self, obj):
        if not obj.agendada_para:
            return ""
        from ..utils.horarios import fuso, DIAS
        d = obj.agendada_para.astimezone(fuso())
        return f"{DIAS[d.weekday()]} {d:%d/%m} às {d:%H:%M}"

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
        return _receita_liquida(obj)
        
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

        # por pagar: só o pagamento a faz avançar. Antes a loja marcava-a "pago" à mão e depois
        # "concluido" — sem pagamento nem comissão (e o prazo de 30 min deixava de a cancelar)
        if status_actual == 'pendente':
            raise serializers.ValidationError(
                'Esta encomenda ainda não foi paga — só pode ser cancelada.'
            )

        # não se volta atrás (o backoffice também não deixa). Voltar a "pendente" fazia o prazo de
        # pagamento cancelar uma encomenda já paga.
        if idx_novo < idx_actual:
            raise serializers.ValidationError(
                'Não é possível retroceder o estado de uma encomenda.'
            )
 
        return value