from rest_framework import serializers
from ..models import CategoriaLoja, CategoriaDestaque, Produto


class CategoriaLojaSerializer(serializers.ModelSerializer):
    total_produtos = serializers.SerializerMethodField()

    class Meta:
        model  = CategoriaLoja
        fields = ['id', 'nome', 'icone', 'ativo', 'ordem', 'total_produtos']

    def get_total_produtos(self, obj):
        return obj.produtos.filter(ativo=True).count()

    def validate_nome(self, value):
        return value.lower().strip()

    def validate_icone(self, value):
        if value and len(value) > 10:
            raise serializers.ValidationError('Ícone demasiado longo.')
        return value or '📂'


class CategoriaLojaMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CategoriaLoja
        fields = ['id', 'nome', 'icone']


class CategoriaDestaqueSerializer(serializers.ModelSerializer):
    # leitura
    nome        = serializers.CharField(source='categoria.nome',       read_only=True)
    icone_final = serializers.CharField(source='icone_display',        read_only=True)
    loja_nome   = serializers.CharField(source='categoria.loja.nome',  read_only=True)
    loja_id     = serializers.IntegerField(source='categoria.loja.id', read_only=True)
    categoria_id = serializers.IntegerField(source='categoria.id',     read_only=True)

    # escrita
    categoria_loja_id = serializers.PrimaryKeyRelatedField(
        queryset=CategoriaLoja.objects.all(),
        source='categoria',
        write_only=True,
    )

    class Meta:
        model  = CategoriaDestaque
        fields = [
            'id', 'nome', 'icone', 'icone_final',
            'ordem', 'ativo',
            'loja_nome', 'loja_id', 'categoria_id',
            'categoria_loja_id',
        ]

    def validate(self, attrs):
        # não permite duplicar a mesma categoria em destaque
        categoria = attrs.get('categoria')
        if categoria:
            qs = CategoriaDestaque.objects.filter(categoria=categoria)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {'categoria_loja_id': 'Esta categoria já está em destaque.'}
                )
        return attrs