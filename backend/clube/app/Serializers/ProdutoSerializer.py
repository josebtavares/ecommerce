import json
from rest_framework import serializers
from ..models import Produto, TipoProduto, Inventario
from .LojaSerializer import LojaMiniSerializer


# ══════════════════════════════════════════════════════════════
# CAMPO CUSTOMIZADO — aceita string JSON ou dict
# ══════════════════════════════════════════════════════════════

class FlexJSONField(serializers.Field):
    """
    Aceita tanto string JSON (vem do FormData/multipart)
    como dict directamente (vem de JSON body).
    """
    def to_internal_value(self, data):
        if isinstance(data, dict):
            return data
        if isinstance(data, str):
            data = data.strip()
            if not data:
                return {}
            try:
                result = json.loads(data)
                if not isinstance(result, dict):
                    raise serializers.ValidationError('atributos deve ser um objecto JSON.')
                return result
            except json.JSONDecodeError:
                raise serializers.ValidationError('atributos: JSON invalido.')
        if data is None:
            return {}
        raise serializers.ValidationError('atributos deve ser um objecto JSON.')

    def to_representation(self, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return {}
        return value or {}


# ══════════════════════════════════════════════════════════════
# TIPO DE PRODUTO
# ══════════════════════════════════════════════════════════════

class TipoProdutoSerializer(serializers.ModelSerializer):
    is_global = serializers.SerializerMethodField()

    class Meta:
        model  = TipoProduto
        fields = ['id', 'nome', 'descricao', 'atributos_schema', 'is_global', 'ativo']
        read_only_fields = ['is_global']

    def get_is_global(self, obj):
        return obj.loja is None

    def validate_atributos_schema(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('atributos_schema deve ser uma lista.')

        normalizado = []
        for item in value:
            if isinstance(item, str):
                normalizado.append({
                    'nome': item, 'tipo': 'texto',
                    'opcoes': [], 'obrigatorio': False,
                })
            elif isinstance(item, dict):
                if not item.get('nome'):
                    raise serializers.ValidationError('Cada atributo precisa de ter um nome.')
                if item.get('tipo') == 'choices' and not item.get('opcoes'):
                    raise serializers.ValidationError(
                        f'Atributo "{item["nome"]}" do tipo choices precisa de ter opcoes.'
                    )
                normalizado.append({
                    'nome':        item['nome'].lower().strip(),
                    'tipo':        item.get('tipo', 'texto'),
                    'opcoes':      item.get('opcoes', []),
                    'obrigatorio': item.get('obrigatorio', False),
                })
            else:
                raise serializers.ValidationError(f'Item invalido: {item}')
        return normalizado

    def validate_nome(self, value):
        return value.lower().strip()


# ══════════════════════════════════════════════════════════════
# PRODUTO
# ══════════════════════════════════════════════════════════════

class ProdutoSerializer(serializers.ModelSerializer):

    # ── Leitura ───────────────────────────────────────────────
    loja               = LojaMiniSerializer(read_only=True)
    tipo               = TipoProdutoSerializer(read_only=True)
    ficheiro_url       = serializers.SerializerMethodField()
    atributos_em_falta = serializers.SerializerMethodField()
    stock              = serializers.SerializerMethodField()

    # ── Escrita ───────────────────────────────────────────────
    tipo_id   = serializers.PrimaryKeyRelatedField(
                    queryset=TipoProduto.objects.filter(ativo=True),
                    source='tipo',
                    write_only=True,
                    required=False,
                    allow_null=True,
                )
    atributos = FlexJSONField(required=False, default=dict)

    class Meta:
        model  = Produto
        fields = [
            'id',
            'loja',
            'tipo', 'tipo_id',
            'nome', 'descricao', 'categoria', 'sku',
            'preco',
            'ficheiro', 'ficheiro_url',
            'atributos', 'atributos_em_falta',
            'stock',
            'destaque', 'ativo',
            'data_criacao',
        ]
        read_only_fields = ['loja', 'data_criacao']
        extra_kwargs = {
            'ficheiro': {'write_only': True, 'required': False},
        }

    def get_ficheiro_url(self, obj):
        request = self.context.get('request')
        if obj.ficheiro and request:
            return request.build_absolute_uri(obj.ficheiro.url)
        return None

    def get_atributos_em_falta(self, obj):
        return obj.atributos_em_falta()

    def get_stock(self, obj):
        try:
            inv = obj.inventario
            return {
                'quantidade'  : inv.quantidade,
                'preco_custo' : str(inv.preco_custo),
                'preco_venda' : str(inv.preco_venda),
            }
        except Inventario.DoesNotExist:
            return None

    def validate_atributos(self, value):
        # aceita string JSON (vem do FormData) ou dict directamente
        if isinstance(value, str):
            if not value or value.strip() in ('', '{}'):
                return {}
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError('atributos: JSON invalido.')
        if isinstance(value, dict):
            return value
        if value is None:
            return {}
        raise serializers.ValidationError('atributos deve ser um objecto JSON.')

    def to_internal_value(self, data):
        # converte atributos de string para dict ANTES da validacao
        # necessario porque FormData envia tudo como string
        if 'atributos' in data and isinstance(data.get('atributos'), str):
            try:
                val = data['atributos'].strip()
                data = data.copy()
                data['atributos'] = json.loads(val) if val else {}
            except (json.JSONDecodeError, AttributeError):
                pass
        return super().to_internal_value(data)

    def validate(self, attrs):
        tipo      = attrs.get('tipo')
        atributos = attrs.get('atributos', {})
        if tipo and atributos:
            em_falta = tipo.validar_atributos(atributos)
            if em_falta:
                raise serializers.ValidationError({
                    'atributos': f'Campos obrigatorios em falta: {em_falta}'
                })
        return attrs

    def to_representation(self, instance):
        # garante que atributos é sempre devolvido como dict na leitura
        ret = super().to_representation(instance)
        if isinstance(ret.get('atributos'), str):
            try:
                ret['atributos'] = json.loads(ret['atributos'])
            except (json.JSONDecodeError, TypeError):
                ret['atributos'] = {}
        return ret

    def create(self, validated_data):
        return Produto.objects.create(**validated_data)

    def update(self, instance, validated_data):
        if 'atributos' in validated_data:
            merged = {**instance.atributos, **validated_data.pop('atributos')}
            instance.atributos = merged
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    
    def validate_categoria(self, value):
        if value:
            return value.lower().strip()
        return value


# ══════════════════════════════════════════════════════════════
# PRODUTO MINI
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