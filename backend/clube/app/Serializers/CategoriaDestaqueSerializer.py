from rest_framework import serializers
from ..models import CategoriaDestaque


class CategoriaDestaqueSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CategoriaDestaque
        fields = ['id', 'nome', 'icone', 'ordem', 'ativo']

    def validate_nome(self, value):
        return value.lower().strip()

    def validate_icone(self, value):
        if value and len(value) > 10:
            raise serializers.ValidationError('Ícone demasiado longo.')
        return value or '📂'