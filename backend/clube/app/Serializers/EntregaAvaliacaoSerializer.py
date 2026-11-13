from rest_framework import serializers
from ..models import (
    OpcaoEntrega, Condutor, Entrega, Transportadora,
    AvaliacaoLoja, Encomenda
)
from .UtilizadorSerializer import UtilizadorMiniSerializer
from ..utils import devolucoes, horarios
from ..utils.encomendas import valor_a_cobrar

# pedido de cancelamento sem resposta (pedido) ou já com a Bendi (em_disputa): o condutor não deve sair
CANCELAMENTO_POR_DECIDIR = ('pedido', 'em_disputa')


# ══════════════════════════════════════════════════════════════
# OPÇÃO DE ENTREGA
# ══════════════════════════════════════════════════════════════

class OpcaoEntregaSerializer(serializers.ModelSerializer):
    # envio por transportadora (utils/envios.py): transportadora da lista ou "Outra" + as ilhas onde serve
    transportadora_id   = serializers.PrimaryKeyRelatedField(
        source='transportadora', queryset=Transportadora.objects.filter(ativa=True),
        required=False, allow_null=True)
    transportadora_nome = serializers.SerializerMethodField()

    class Meta:
        model  = OpcaoEntrega
        fields = [
            'id', 'nome', 'preco',
            'tempo_estimado', 'area_cobertura', 'ativa',
            'tipo', 'transportadora_id', 'transportadora_nome', 'transportadora_outra', 'ilhas',
        ]

    def get_transportadora_nome(self, obj):
        from ..utils.envios import nome_transportadora
        return nome_transportadora(obj.transportadora, obj.transportadora_outra)

    def validate_preco(self, value):
        if value < 0:
            raise serializers.ValidationError('O preço não pode ser negativo.')
        return value

    def validate_ilhas(self, value):
        from ..utils.envios import ErroEnvio, limpar_ilhas
        try:
            return limpar_ilhas(value)
        except ErroEnvio as e:
            raise serializers.ValidationError(str(e))

    def validate(self, attrs):
        inst = self.instance
        tipo = attrs.get('tipo', inst.tipo if inst else 'local')
        if tipo == 'envio':
            t = attrs['transportadora'] if 'transportadora' in attrs else (inst.transportadora if inst else None)
            outra = (attrs.get('transportadora_outra', inst.transportadora_outra if inst else '') or '').strip()
            if not t and len(outra) < 2:
                raise serializers.ValidationError({'transportadora_id': 'Escolhe a transportadora (ou escreve o nome em "Outra").'})
            if t:
                attrs['transportadora_outra'] = ''
            ilhas = attrs['ilhas'] if 'ilhas' in attrs else (inst.ilhas if inst else [])
            if not ilhas:
                raise serializers.ValidationError({'ilhas': 'Escolhe pelo menos uma ilha para onde envias.'})
        elif 'tipo' in attrs:
            attrs['transportadora'], attrs['transportadora_outra'] = None, ''
        return attrs


# ══════════════════════════════════════════════════════════════
# CONDUTOR
# ══════════════════════════════════════════════════════════════

class CondutorSerializer(serializers.ModelSerializer):
    utilizador = UtilizadorMiniSerializer(read_only=True)
    utilizador_id = serializers.IntegerField(write_only=True)
    utilizador_nome     = serializers.CharField(source='utilizador.nome',         read_only=True)
    utilizador_username = serializers.CharField(source='utilizador.user.username', read_only=True)

    utilizador_email    = serializers.CharField(source='utilizador.user.email',    read_only=True)
    utilizador_telefone = serializers.CharField(source='utilizador.telefone',      read_only=True)
    class Meta:
        model  = Condutor
        fields = [
            'id', 'utilizador', 'utilizador_id',
            'tipo_veiculo', 'ativo',
            'utilizador_nome', 'utilizador_username',
            'utilizador_email', 'utilizador_telefone',
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
    
    # campos do comprador da encomenda
    comprador_nome     = serializers.SerializerMethodField()
    comprador_email    = serializers.SerializerMethodField()
    comprador_telefone = serializers.SerializerMethodField()
    morada_entrega     = serializers.CharField(source='encomenda.morada_entrega', read_only=True)
    cliente_nif        = serializers.CharField(source='encomenda.cliente_nif', read_only=True)
    notas              = serializers.CharField(source='encomenda.notas', read_only=True)
    tipo_entrega       = serializers.CharField(source='encomenda.tipo_entrega', read_only=True)
    metodo_pagamento   = serializers.SerializerMethodField()
    # o que o condutor precisa de saber sem abrir a encomenda
    comprador_id       = serializers.IntegerField(source='encomenda.comprador_id', read_only=True)
    itens              = serializers.SerializerMethodField()
    valor_a_cobrar     = serializers.SerializerMethodField()
    pago               = serializers.SerializerMethodField()
    agendada_para      = serializers.DateTimeField(source='encomenda.agendada_para', read_only=True)
    agendada_texto     = serializers.SerializerMethodField()
    motivo_falha_texto = serializers.CharField(source='get_motivo_falha_display', read_only=True)
    encomenda_status   = serializers.CharField(source='encomenda.status', read_only=True)
    # campos da opção de entrega (flat — mais fácil de usar no frontend)
    opcao_entrega_nome  = serializers.CharField(source='opcao_entrega.nome',           read_only=True)
    opcao_entrega_tempo = serializers.CharField(source='opcao_entrega.tempo_estimado',  read_only=True)
    opcao_entrega_preco = serializers.DecimalField(source='opcao_entrega.preco', max_digits=10, decimal_places=2, read_only=True)
    # campos do condutor (flat)
    condutor_nome     = serializers.SerializerMethodField()
    valor_recebido    = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    acertado_em       = serializers.SerializerMethodField()
    prova             = serializers.SerializerMethodField()
    pode_juntar_prova = serializers.SerializerMethodField()
    # o cliente pediu para cancelar e a loja ainda não respondeu (o condutor não deve sair sem falar com a loja)
    cancelamento_pedido = serializers.SerializerMethodField()
    condutor_veiculo  = serializers.SerializerMethodField()
    condutor_id_field = serializers.SerializerMethodField()
    tipo              = serializers.CharField(read_only=True)        # 'condutor' | 'envio' (utils/envios.py)
    envio             = serializers.SerializerMethodField()
    data_criacao      = serializers.DateTimeField(format='%d-%m-%Y %H:%M', read_only=True)
    data_entrega      = serializers.DateTimeField(format='%d-%m-%Y %H:%M', read_only=True)

    class Meta:
        model  = Entrega
        fields = [
            'id', 'encomenda',
            'condutor', 'condutor_id',
            'opcao_entrega', 'opcao_entrega_id',
            'status',
            'data_criacao', 'data_entrega',
            'comprador_nome', 'comprador_email', 'comprador_telefone',
            'morada_entrega', 'cliente_nif', 'notas', 'tipo_entrega', 'metodo_pagamento',
            'comprador_id', 'itens', 'valor_a_cobrar', 'pago', 'encomenda_status', 'agendada_para', 'agendada_texto',
            'motivo_falha', 'motivo_falha_texto', 'nota_falha',
            'opcao_entrega_nome', 'opcao_entrega_tempo', 'opcao_entrega_preco',
            'condutor_nome', 'condutor_veiculo', 'condutor_id_field',
            'valor_recebido', 'acertado_em', 'prova', 'pode_juntar_prova', 'cancelamento_pedido',
            'tipo', 'envio',
        ]
        read_only_fields = ['data_criacao']

    def get_envio(self, obj):
        from ..utils import envios
        return envios.dados(obj, self.context.get('request'), loja=True)

    def validate_status(self, value):
        instancia = self.instance
        if not instancia:
            return value
 
        transicoes = {
            'atribuido' : ['a_caminho', 'entregue', 'falhou'],
            'a_caminho' : ['entregue', 'falhou'],
            'entregue'  : [],
            'cancelada' : [],
            'devolvida' : [],
            'falhou'    : [],     # só a loja volta a pôr em curso, ao reatribuir (entrega_criar/entrega_atualizar)
        }
        permitidos = transicoes.get(instancia.status, [])
        if value != instancia.status and value not in permitidos:
            raise serializers.ValidationError(
                f'Transição inválida: {instancia.status} → {value}. '
                f'Permitidos: {permitidos}'
            )
        return value
    
    def get_prova(self, obj):
        from ..utils import prova_entrega
        return prova_entrega.dados(obj, self.context.get('request'))

    def get_pode_juntar_prova(self, obj):
        from ..utils import prova_entrega
        return prova_entrega.pode_juntar(obj) is None and not (obj.prova_foto and obj.prova_assinatura
                                                                 and obj.recebido_por_nome)

    def get_cancelamento_pedido(self, obj):
        if obj.status not in ('atribuido', 'a_caminho'):
            return False
        anotado = getattr(obj, 'cancelamento_pedido_anot', None)
        if anotado is not None:
            return anotado
        return obj.encomenda.reembolsos.filter(tipo='cancelamento', estado__in=CANCELAMENTO_POR_DECIDIR).exists()

    def get_comprador_nome(self, obj):
        try:
            return obj.encomenda.comprador.user.get_full_name() or obj.encomenda.comprador.user.username
        except Exception:
            return None

    def get_comprador_email(self, obj):
        try:
            return obj.encomenda.comprador.user.email
        except Exception:
            return None

    def get_comprador_telefone(self, obj):
        try:
            return obj.encomenda.comprador.telefone
        except Exception:
            return None

    def get_metodo_pagamento(self, obj):
        try:
            return obj.encomenda.pagamento.metodo.tipo
        except Exception:
            return None

    def get_itens(self, obj):
        # o que ficou por entregar: os esgotados saem da encomenda
        qtd = devolucoes.qtd_disponivel(obj.encomenda)
        return [f'{qtd[i.id]}× {i.produto.nome if i.produto else "Produto removido"}'
                for i in obj.encomenda.itens.all() if qtd[i.id] > 0]

    def get_valor_a_cobrar(self, obj):
        valor = valor_a_cobrar(obj.encomenda)
        return str(valor) if valor is not None else None

    def get_pago(self, obj):
        try:
            return obj.encomenda.pagamento.status == 'aprovado'
        except Exception:
            return False

    def get_agendada_texto(self, obj):
        return horarios.texto_agendada(obj.encomenda.agendada_para)

    def get_condutor_nome(self, obj):
        try:
            return obj.condutor.utilizador.user.get_full_name() or obj.condutor.utilizador.user.username
        except Exception:
            return None

    def get_acertado_em(self, obj):
        """Dinheiro cobrado já entregue à loja (acerto não anulado): quando."""
        a = obj.acerto if obj.acerto_id else None
        return a.criado_em if a and not a.anulado else None

    def get_condutor_veiculo(self, obj):
        try:
            return obj.condutor.tipo_veiculo
        except Exception:
            return None

    def get_condutor_id_field(self, obj):
        try:
            return obj.condutor.id
        except Exception:
            return None
    
    
    
    


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
    utilizador_username = serializers.SerializerMethodField()
    utilizador_foto = serializers.SerializerMethodField()

    def get_utilizador_username(self, obj):
        # conta apagada (utils/eliminacao.py): a avaliação fica e conta na nota, sem o nome
        return 'Utilizador eliminado' if obj.utilizador.status == 'eliminado' else obj.utilizador.user.username
 
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