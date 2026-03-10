import json
from rest_framework import serializers
from ..models import Produto, TipoProduto, Inventario


# ══════════════════════════════════════════════════════════════
# TIPO DE PRODUTO
# ══════════════════════════════════════════════════════════════

class TipoProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = TipoProduto
        fields = ['id', 'nome', 'descricao', 'atributos_schema', 'ativo']


# ══════════════════════════════════════════════════════════════
# PRODUTO
# ══════════════════════════════════════════════════════════════

class ProdutoSerializer(serializers.ModelSerializer):

    # ── Leitura ───────────────────────────────────────────────
    tipo        = TipoProdutoSerializer(read_only=True)
    ficheiro_url= serializers.SerializerMethodField()
    atributos_em_falta = serializers.SerializerMethodField()
    stock       = serializers.SerializerMethodField()

    # ── Escrita ───────────────────────────────────────────────
    tipo_id     = serializers.PrimaryKeyRelatedField(
                    queryset=TipoProduto.objects.filter(ativo=True),
                    source='tipo',
                    write_only=True,
                    required=False,
                    allow_null=True,
                  )
    # atributos aceita dict directamente ou JSON string (vindo de FormData)
    atributos   = serializers.JSONField(required=False, default=dict)

    class Meta:
        model  = Produto
        fields = [
            'id',
            # relações
            'loja',
            'tipo', 'tipo_id',
            # dados base
            'nome', 'descricao', 'categoria', 'sku',
            'preco',
            # media
            'ficheiro', 'ficheiro_url',
            # atributos dinâmicos
            'atributos', 'atributos_em_falta',
            # stock (leitura — vem do Inventario)
            'stock',
            # flags
            'destaque', 'ativo',
            'data_criacao',
        ]
        read_only_fields = ['loja', 'data_criacao']
        extra_kwargs = {
            'ficheiro': {'write_only': True, 'required': False},
        }

    # ── SerializerMethodFields ────────────────────────────────

    def get_ficheiro_url(self, obj):
        request = self.context.get('request')
        if obj.ficheiro and request:
            return request.build_absolute_uri(obj.ficheiro.url)
        return None

    def get_atributos_em_falta(self, obj):
        """Mostra campos do schema que ainda não foram preenchidos."""
        return obj.atributos_em_falta()

    def get_stock(self, obj):
        """
        Devolve dados de inventário se existirem.
        Evita query extra com select_related('inventario') na view.
        """
        try:
            inv = obj.inventario
            return {
                'quantidade'  : inv.quantidade,
                'preco_custo' : str(inv.preco_custo),
                'preco_venda' : str(inv.preco_venda),
            }
        except Inventario.DoesNotExist:
            return None

    # ── Validação ─────────────────────────────────────────────

    def validate_atributos(self, value):
        """Aceita dict ou JSON string (FormData envia strings)."""
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError('atributos: JSON inválido.')
        if not isinstance(value, dict):
            raise serializers.ValidationError('atributos deve ser um objecto JSON.')
        return value

    def validate(self, attrs):
        """
        Valida os atributos contra o schema do tipo escolhido.
        Só bloqueia se o tipo tiver schema definido E os atributos
        forem enviados — permite criação parcial (draft).
        """
        tipo      = attrs.get('tipo')
        atributos = attrs.get('atributos', {})

        if tipo and atributos:
            em_falta = tipo.validar_atributos(atributos)
            if em_falta:
                raise serializers.ValidationError({
                    'atributos': f'Campos obrigatórios em falta: {em_falta}'
                })
        return attrs

    # ── Create / Update ───────────────────────────────────────

    def create(self, validated_data):
        # loja é injectada pela view via serializer.save(loja=loja)
        return Produto.objects.create(**validated_data)

    def update(self, instance, validated_data):
        # merge dos atributos JSON — não substitui tudo, só actualiza as chaves enviadas
        if 'atributos' in validated_data:
            merged = {**instance.atributos, **validated_data.pop('atributos')}
            instance.atributos = merged

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# ══════════════════════════════════════════════════════════════
# PRODUTO MINI  (usado em listagens de encomendas, carrinho, etc.)
# ══════════════════════════════════════════════════════════════

class ProdutoMiniSerializer(serializers.ModelSerializer):
    ficheiro_url = serializers.SerializerMethodField()
    tipo_nome    = serializers.CharField(source='tipo.nome', read_only=True)

    class Meta:
        model  = Produto
        fields = ['id', 'nome', 'preco', 'ficheiro_url', 'tipo_nome', 'atributos']

    def get_ficheiro_url(self, obj):
        request = self.context.get('request')
        if obj.ficheiro and request:
            return request.build_absolute_uri(obj.ficheiro.url)
        return None