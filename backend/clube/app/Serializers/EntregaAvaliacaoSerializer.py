from rest_framework import serializers
from ..models import (
    OpcaoEntrega, Condutor, Entrega,
    AvaliacaoLoja, Encomenda
)
from .UtilizadorSerializer import UtilizadorMiniSerializer


# ══════════════════════════════════════════════════════════════
# OPÇÃO DE ENTREGA
# ══════════════════════════════════════════════════════════════

class OpcaoEntregaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = OpcaoEntrega
        fields = [
            'id', 'nome', 'preco',
            'tempo_estimado', 'area_cobertura', 'ativa',
        ]

    def validate_preco(self, value):
        if value < 0:
            raise serializers.ValidationError('O preço não pode ser negativo.')
        return value


# ══════════════════════════════════════════════════════════════
# CONDUTOR
# ══════════════════════════════════════════════════════════════

class CondutorSerializer(serializers.ModelSerializer):
    utilizador = UtilizadorMiniSerializer(read_only=True)
    utilizador_id = serializers.IntegerField(write_only=True)
    utilizador_nome     = serializers.CharField(source='utilizador.nome',         read_only=True)
    utilizador_username = serializers.CharField(source='utilizador.user.username', read_only=True)

    class Meta:
        model  = Condutor
        fields = [
            'id', 'utilizador', 'utilizador_id',
            'tipo_veiculo', 'ativo',
            'utilizador_nome', 'utilizador_username',
        ]

    def validate_utilizador_id(self, value):
        from ..models import Utilizador
        if not Utilizador.objects.filter(id=value, status='ativo').exists():
            raise serializers.ValidationError('Utilizador não encontrado ou inactivo.')
        return value

    def create(self, validated_data):
        from ..models import Utilizador
        utilizador_id = validated_data.pop('utilizador_id')
        utilizador    = Utilizador.objects.get(id=utilizador_id)
        return Condutor.objects.create(utilizador=utilizador, **validated_data)


# ══════════════════════════════════════════════════════════════
# ENTREGA
# ══════════════════════════════════════════════════════════════

class EntregaSerializer(serializers.ModelSerializer):
    condutor      = CondutorSerializer(read_only=True)
    opcao_entrega = OpcaoEntregaSerializer(read_only=True)

    # escrita
    condutor_id      = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    opcao_entrega_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model  = Entrega
        fields = [
            'id', 'encomenda',
            'condutor', 'condutor_id',
            'opcao_entrega', 'opcao_entrega_id',
            'status',
            'data_criacao', 'data_entrega',
        ]
        read_only_fields = ['data_criacao']

    def validate_status(self, value):
        instancia = self.instance
        if not instancia:
            return value
 
        transicoes = {
            'atribuido' : ['a_caminho', 'entregue', 'falhou'],
            'a_caminho' : ['entregue', 'falhou'],
            'entregue'  : [],
            'falhou'    : ['atribuido'],  # permite reatribuir após falha
        }
        permitidos = transicoes.get(instancia.status, [])
        if value != instancia.status and value not in permitidos:
            raise serializers.ValidationError(
                f'Transição inválida: {instancia.status} → {value}. '
                f'Permitidos: {permitidos}'
            )
        return value


# ══════════════════════════════════════════════════════════════
# AVALIAÇÃO
# ══════════════════════════════════════════════════════════════

class AvaliacaoLojaSerializer(serializers.ModelSerializer):
    utilizador = UtilizadorMiniSerializer(read_only=True)
    loja_nome  = serializers.CharField(source='loja.nome', read_only=True)
    encomenda_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
 
    class Meta:
        model  = AvaliacaoLoja
        fields = [
            'id',
            'utilizador',
            'loja', 'loja_nome',
            'encomenda', 'encomenda_id',
            'pontuacao', 'comentario',
            'data_criacao',
        ]
        read_only_fields = ['utilizador', 'data_criacao', 'encomenda']
 
    def validate_pontuacao(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError('A pontuação deve ser entre 1 e 5.')
        return value
 
    def validate(self, attrs):
        request    = self.context.get('request')
        utilizador = request.user.utilizador
        loja       = attrs.get('loja')
 
        # na edição (instance já existe) — só valida pontuação/comentário
        if self.instance:
            return attrs
 
        # na criação — valida encomenda
        encomenda_id = attrs.get('encomenda_id')
        if not encomenda_id:
            raise serializers.ValidationError(
                {'encomenda_id': 'Indica a encomenda que queres avaliar.'}
            )
 
        from ..models import Encomenda
        try:
            encomenda = Encomenda.objects.get(id=encomenda_id)
        except Encomenda.DoesNotExist:
            raise serializers.ValidationError({'encomenda_id': 'Encomenda não encontrada.'})
 
        if encomenda.status != 'concluido':
            raise serializers.ValidationError(
                {'encomenda_id': 'Só podes avaliar encomendas concluídas.'}
            )
        if encomenda.comprador != utilizador:
            raise serializers.ValidationError(
                {'encomenda_id': 'Só podes avaliar as tuas próprias encomendas.'}
            )
        if loja and encomenda.loja != loja:
            raise serializers.ValidationError(
                {'encomenda_id': 'Esta encomenda não pertence à loja indicada.'}
            )
        if AvaliacaoLoja.objects.filter(utilizador=utilizador, encomenda=encomenda).exists():
            raise serializers.ValidationError(
                {'encomenda_id': 'Já avaliaste esta encomenda.'}
            )
 
        attrs['encomenda'] = encomenda
        return attrs
 
    def create(self, validated_data):
        validated_data.pop('encomenda_id', None)
        validated_data['utilizador'] = self.context['request'].user.utilizador
        return super().create(validated_data)


class AvaliacaoMiniSerializer(serializers.ModelSerializer):
    utilizador_username = serializers.CharField(
        source='utilizador.user.username', read_only=True
    )
    utilizador_foto = serializers.SerializerMethodField()
 
    class Meta:
        model  = AvaliacaoLoja
        fields = [
            'id', 'utilizador_username', 'utilizador_foto',
            'pontuacao', 'comentario', 'data_criacao',
            'oculta',
        ]
 
    def get_utilizador_foto(self, obj):
        request = self.context.get('request')
        if obj.utilizador.foto:
            url = obj.utilizador.foto.url
            return request.build_absolute_uri(url) if request else url
        return None