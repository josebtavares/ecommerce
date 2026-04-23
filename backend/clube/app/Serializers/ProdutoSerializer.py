import json
from rest_framework import serializers
from ..models import Produto, TipoProduto, Inventario, CategoriaLoja, ProdutoImagem
from .LojaSerializer import LojaMiniSerializer
from ..Serializers.CategoriaLojaSerializer import CategoriaLojaMiniSerializer


# ══════════════════════════════════════════════════════════════
# CAMPO CUSTOMIZADO — aceita string JSON ou dict
# ══════════════════════════════════════════════════════════════

class FlexJSONField(serializers.Field):
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
# IMAGEM DE PRODUTO  ← NOVO
# ══════════════════════════════════════════════════════════════

class ProdutoImagemSerializer(serializers.ModelSerializer):
    ficheiro_url = serializers.SerializerMethodField()

    class Meta:
        model  = ProdutoImagem
        fields = ['id', 'ficheiro_url', 'ordem', 'legenda']

    def get_ficheiro_url(self, obj):
        request = self.context.get('request')
        if obj.ficheiro and request:
            return request.build_absolute_uri(obj.ficheiro.url)
        if obj.ficheiro:
            return obj.ficheiro.url
        return None


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

    # ── NOVO: imagens adicionais + atributos normalizados ──────
    imagens                = ProdutoImagemSerializer(many=True, read_only=True)
    atributos_normalizados = serializers.SerializerMethodField()

    # ── Escrita ───────────────────────────────────────────────
    tipo_id = serializers.PrimaryKeyRelatedField(
        queryset=TipoProduto.objects.filter(ativo=True),
        source='tipo',
        write_only=True,
        required=False,
        allow_null=True,
    )
    atributos = FlexJSONField(required=False, default=dict)
    categorias = CategoriaLojaMiniSerializer(many=True, read_only=True)
    categoria_ids = serializers.PrimaryKeyRelatedField(
        queryset=CategoriaLoja.objects.all(),
        many=True,
        write_only=True,
        required=False,
        source='categorias',
    )

    class Meta:
        model  = Produto
        fields = [
            'id',
            'loja',
            'tipo', 'tipo_id',
            'nome', 'descricao', 'sku',
            'preco',
            'ficheiro', 'ficheiro_url',
            'imagens',                    # ← NOVO
            'atributos', 'atributos_normalizados', 'atributos_em_falta',  # ← atributos_normalizados novo
            'stock',
            'destaque', 'ativo',
            'data_criacao',
            'categorias', 'categoria_ids',
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

    def get_atributos_normalizados(self, obj):
        """
        Garante que cada valor é sempre uma lista, independentemente
        do formato guardado na BD:
          formato antigo → {"cor": "vermelho"}       → {"cor": ["vermelho"]}
          formato novo   → {"cor": ["vermelho","azul"]} → inalterado
        O frontend (productInfoCard) usa este campo para filtrar
        quais as opções disponíveis num produto específico.
        """
        raw = obj.atributos or {}
        normalized = {}
        for key, val in raw.items():
            if isinstance(val, list):
                normalized[key] = [str(v) for v in val if v is not None and str(v).strip()]
            elif val is not None and str(val).strip():
                normalized[key] = [str(val)]
            else:
                normalized[key] = []
        return normalized

    def validate_atributos(self, value):
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
        ret = super().to_representation(instance)
        if isinstance(ret.get('atributos'), str):
            try:
                ret['atributos'] = json.loads(ret['atributos'])
            except (json.JSONDecodeError, TypeError):
                ret['atributos'] = {}
        return ret

    def create(self, validated_data):
        categorias = validated_data.pop('categorias', [])
        produto = Produto.objects.create(**validated_data)
        if categorias:
            produto.categorias.set(categorias)
        return produto

    def update(self, instance, validated_data):
        categorias = validated_data.pop('categorias', None)
        if 'atributos' in validated_data:
            merged = {**instance.atributos, **validated_data.pop('atributos')}
            instance.atributos = merged
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if categorias is not None:
            instance.categorias.set(categorias)
        return instance


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