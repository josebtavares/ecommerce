"""
Serializers do Sistema POS
Conversão entre modelos Django e JSON para API REST
"""
from rest_framework import serializers
from .models import (
    ConfiguracaoPOS,
    Mesa,
    ContaMesa,
    ItemContaMesa,
    PagamentoDividido,
    TurnoPOS,
    UtilizadorPOS,       # ← NOVO: importar modelo atualizado
)
from app.models import Loja, Produto, Utilizador


# ═══════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO POS
# ═══════════════════════════════════════════════════════════════════

class LojaSimplificadaSerializer(serializers.ModelSerializer):
    """Loja simplificada para uso em outros serializers"""
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Loja
        fields = ['id', 'nome', 'logo_url']

    def get_logo_url(self, obj):
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None


class ConfiguracaoPOSSerializer(serializers.ModelSerializer):
    """Serializer completo para ConfiguracaoPOS"""
    loja_vinculada = LojaSimplificadaSerializer(read_only=True)
    dono_nome = serializers.CharField(source='dono.nome', read_only=True)

    class Meta:
        model = ConfiguracaoPOS
        fields = [
            'id',
            'codigo_pos',
            'nome',
            'dono',
            'dono_nome',
            'loja_vinculada',
            'modo',
            'taxa_servico_ativa',
            'taxa_servico_percentagem',
            'efatura_ativo',
            'efatura_nif',
            'ativo',
            'criado_em',
            'atualizado_em',
        ]
        read_only_fields = ['codigo_pos', 'criado_em', 'atualizado_em']
        extra_kwargs = {
            'efatura_api_key': {'write_only': True}
        }


class ConfiguracaoPOSCreateSerializer(serializers.Serializer):
    """Serializer para criar novo POS"""
    nome = serializers.CharField(max_length=100, default='POS Principal')
    loja_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_loja_id(self, value):
        if value:
            request = self.context.get('request')
            if not Loja.objects.filter(id=value, dono=request.user.utilizador).exists():
                raise serializers.ValidationError('Loja não encontrada ou não pertence ao utilizador')
        return value


# ═══════════════════════════════════════════════════════════════════
# MESAS
# ═══════════════════════════════════════════════════════════════════

class UtilizadorSimplificadoSerializer(serializers.ModelSerializer):
    """Utilizador Bendi simplificado para uso em outros serializers"""
    class Meta:
        model = Utilizador
        fields = ['id', 'nome']


class MesaSerializer(serializers.ModelSerializer):
    """Serializer completo para Mesa"""
    atendente_atual = UtilizadorSimplificadoSerializer(read_only=True)
    tem_conta_aberta = serializers.SerializerMethodField()
    pos_nome = serializers.CharField(source='pos.nome', read_only=True)

    class Meta:
        model = Mesa
        fields = [
            'id',
            'pos',
            'pos_nome',
            'numero',
            'capacidade',
            'status',
            'atendente_atual',
            'aberta_em',
            'ativa',
            'tem_conta_aberta',
            'criada_em',
            'atualizada_em',
        ]
        read_only_fields = ['criada_em', 'atualizada_em']

    def get_tem_conta_aberta(self, obj):
        return ContaMesa.objects.filter(mesa=obj, status='aberta').exists()


class MesaCreateSerializer(serializers.Serializer):
    """Serializer para criar nova mesa"""
    numero = serializers.CharField(max_length=10)
    capacidade = serializers.IntegerField(min_value=1, max_value=20, default=4)


# ═══════════════════════════════════════════════════════════════════
# PRODUTOS
# ═══════════════════════════════════════════════════════════════════

class ProdutoSerializer(serializers.ModelSerializer):
    """Serializer para produtos (compatível com ProductCatalog)"""
    categoria = serializers.SerializerMethodField()
    imagem_url = serializers.SerializerMethodField()
    disponivel = serializers.SerializerMethodField()

    class Meta:
        model = Produto
        fields = [
            'id',
            'nome',
            'descricao',
            'preco',
            'categoria',
            'imagem_url',
            'stock',
            'disponivel',
        ]

    def get_categoria(self, obj):
        if hasattr(obj, 'categoria') and obj.categoria:
            return obj.categoria.nome
        return 'Sem categoria'

    def get_imagem_url(self, obj):
        if obj.imagem:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.imagem.url)
            return obj.imagem.url
        return None

    def get_disponivel(self, obj):
        if hasattr(obj, 'stock'):
            return obj.stock > 0
        return True


# ═══════════════════════════════════════════════════════════════════
# CONTAS E ITEMS
# ═══════════════════════════════════════════════════════════════════

class ItemContaMesaSerializer(serializers.ModelSerializer):
    """Serializer para items da conta"""
    produto_nome = serializers.CharField(source='produto.nome', read_only=True)
    produto_imagem = serializers.SerializerMethodField()
    origem = serializers.SerializerMethodField()

    class Meta:
        model = ItemContaMesa
        fields = [
            'id',
            'conta',
            'produto',
            'produto_nome',
            'produto_imagem',
            'nome',
            'quantidade',
            'preco_unitario',
            'preco_total',
            'observacoes',
            'atribuido_pessoa',
            'origem',
            'status',
            'criado_em',
            'atualizado_em',
        ]
        read_only_fields = ['preco_total', 'criado_em', 'atualizado_em']

    def get_produto_imagem(self, obj):
        ficheiro = obj.produto.imagem if obj.produto and hasattr(obj.produto, 'imagem') else None
        if not ficheiro:
            ficheiro = getattr(obj.produto, 'ficheiro', None) if obj.produto else None
        if ficheiro:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(ficheiro.url)
            return ficheiro.url
        return None

    def get_origem(self, obj):
        return obj.origem  # property no modelo: 'pos' ou 'loja'


class ItemContaMesaCreateSerializer(serializers.Serializer):
    """Serializer para adicionar item à conta"""
    produto_id = serializers.IntegerField()
    quantidade = serializers.IntegerField(min_value=1, default=1)
    observacoes = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_produto_id(self, value):
        if not Produto.objects.filter(id=value).exists():
            raise serializers.ValidationError('Produto não encontrado')
        return value


class ContaMesaSerializer(serializers.ModelSerializer):
    """Serializer completo para Conta de Mesa"""
    mesa = MesaSerializer(read_only=True)
    atendente = UtilizadorSimplificadoSerializer(read_only=True)
    items = ItemContaMesaSerializer(many=True, read_only=True)
    pos_nome = serializers.CharField(source='pos.nome', read_only=True)

    class Meta:
        model = ContaMesa
        fields = [
            'id',
            'pos',
            'pos_nome',
            'mesa',
            'atendente',
            'subtotal',
            'taxa_servico_percentagem',
            'taxa_servico_valor',
            'gorjeta',
            'desconto_valor',
            'total',
            'status',
            'metodo_pagamento',
            'dividida_em',
            'nif_cliente',
            'efatura_processada',
            'efatura_codigo',
            'efatura_url',
            'observacoes',
            'items',
            'criada_em',
            'atualizada_em',
            'fechada_em',
        ]
        read_only_fields = [
            'subtotal',
            'taxa_servico_valor',
            'total',
            'criada_em',
            'atualizada_em',
            'fechada_em',
        ]


class ContaMesaFecharSerializer(serializers.Serializer):
    """Serializer para fechar conta"""
    metodo_pagamento = serializers.ChoiceField(
        choices=['dinheiro', 'cartao', 'mbway', 'transferencia', 'dividida']
    )
    nif_cliente = serializers.CharField(max_length=20, required=False, allow_blank=True)


# ═══════════════════════════════════════════════════════════════════
# PAGAMENTOS DIVIDIDOS
# ═══════════════════════════════════════════════════════════════════

class PagamentoDivididoSerializer(serializers.ModelSerializer):
    """Serializer para pagamentos divididos"""
    class Meta:
        model = PagamentoDividido
        fields = [
            'id',
            'conta',
            'pessoa_numero',
            'valor',
            'metodo',
            'pago',
            'pago_em',
            'criado_em',
        ]
        read_only_fields = ['pago_em', 'criado_em']


# ═══════════════════════════════════════════════════════════════════
# TURNOS
# ═══════════════════════════════════════════════════════════════════

class TurnoPOSSerializer(serializers.ModelSerializer):
    """Serializer para turnos POS"""
    operador = UtilizadorSimplificadoSerializer(read_only=True)
    pos_nome = serializers.CharField(source='pos.nome', read_only=True)

    class Meta:
        model = TurnoPOS
        fields = [
            'id',
            'pos',
            'pos_nome',
            'operador',
            'valor_abertura',
            'valor_fecho',
            'diferenca',
            'aberto',
            'aberto_em',
            'fechado_em',
            'observacoes',
        ]
        read_only_fields = ['diferenca', 'aberto_em', 'fechado_em']


class TurnoAbrirSerializer(serializers.Serializer):
    """Serializer para abrir turno"""
    valor_abertura = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)


class TurnoFecharSerializer(serializers.Serializer):
    """Serializer para fechar turno"""
    valor_fecho = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)


# ═══════════════════════════════════════════════════════════════════
# EQUIPA POS — NOVO MODELO (username + password, sem email/Bendi)
# ═══════════════════════════════════════════════════════════════════

class UtilizadorPOSSerializer(serializers.ModelSerializer):
    """
    Serializer de leitura para membros da equipa POS.
    Nunca expõe password_pos.
    """
    papel_display = serializers.CharField(source='get_papel_display', read_only=True)

    class Meta:
        model = UtilizadorPOS
        fields = [
            'id',
            'nome',
            'username_pos',
            'papel',
            'papel_display',
            'ativo',
            # Permissões granulares
            'pode_abrir_mesas',
            'pode_fechar_contas',
            'pode_cancelar_items',
            'pode_dar_descontos',
            'pode_gerir_produtos',
            'pode_gerir_mesas',
            'pode_gerir_utilizadores',
            'pode_ver_relatorios',
            'pode_abrir_fechar_turno',
            'pode_ver_pedidos',
            'pode_atualizar_status_items',
            'criado_em',
        ]
        # password_pos NUNCA é incluída — nem em escrita
        read_only_fields = ['criado_em', 'papel_display']


class UtilizadorPOSCreateSerializer(serializers.Serializer):
    """
    Serializer de escrita para criar membro da equipa.
    Aceita password opcional (gera automaticamente se omitida).
    """
    nome = serializers.CharField(max_length=100)
    username_pos = serializers.CharField(max_length=50)
    password = serializers.CharField(
        max_length=128,
        required=False,
        allow_blank=True,
        write_only=True,
    )
    papel = serializers.ChoiceField(
        choices=['gerente', 'empregado', 'cozinha', 'caixa'],
        default='empregado',
    )

    def validate_username_pos(self, value):
        # Normalizar para minúsculas
        value = value.strip().lower()

        if len(value) < 3:
            raise serializers.ValidationError('Username deve ter pelo menos 3 caracteres.')

        allowed = set('abcdefghijklmnopqrstuvwxyz0123456789_.')
        if not all(c in allowed for c in value):
            raise serializers.ValidationError(
                'Username só pode conter letras, números, _ e .'
            )

        return value


class UtilizadorPOSUpdateSerializer(serializers.Serializer):
    """
    Serializer de escrita para atualizar membro da equipa.
    Todos os campos são opcionais.
    password só é atualizada se fornecida e não vazia.
    """
    nome = serializers.CharField(max_length=100, required=False)
    username_pos = serializers.CharField(max_length=50, required=False)
    password = serializers.CharField(
        max_length=128,
        required=False,
        allow_blank=True,
        write_only=True,
    )
    papel = serializers.ChoiceField(
        choices=['gerente', 'empregado', 'cozinha', 'caixa'],
        required=False,
    )
    ativo = serializers.BooleanField(required=False)

    # Permissões individuais (override)
    pode_abrir_mesas          = serializers.BooleanField(required=False)
    pode_fechar_contas        = serializers.BooleanField(required=False)
    pode_cancelar_items       = serializers.BooleanField(required=False)
    pode_dar_descontos        = serializers.BooleanField(required=False)
    pode_gerir_produtos       = serializers.BooleanField(required=False)
    pode_gerir_mesas          = serializers.BooleanField(required=False)
    pode_gerir_utilizadores   = serializers.BooleanField(required=False)
    pode_ver_relatorios       = serializers.BooleanField(required=False)
    pode_abrir_fechar_turno   = serializers.BooleanField(required=False)
    pode_ver_pedidos          = serializers.BooleanField(required=False)
    pode_atualizar_status_items = serializers.BooleanField(required=False)

    def validate_username_pos(self, value):
        value = value.strip().lower()
        if len(value) < 3:
            raise serializers.ValidationError('Username deve ter pelo menos 3 caracteres.')
        allowed = set('abcdefghijklmnopqrstuvwxyz0123456789_.')
        if not all(c in allowed for c in value):
            raise serializers.ValidationError('Username só pode conter letras, números, _ e .')
        return value


class UtilizadorPOSLoginSerializer(serializers.Serializer):
    """
    Serializer para login de membro de equipa.
    username + password (+ pos_id opcional se username em vários POS)
    """
    username = serializers.CharField(max_length=50)
    password = serializers.CharField(max_length=128, write_only=True)
    pos_id   = serializers.IntegerField(required=False, allow_null=True)