from rest_framework import serializers
from ..models import Galeria, Utilizador
from django.utils import timezone
from django.core.exceptions import ValidationError

class GaleriaSerializer(serializers.ModelSerializer):
    # devolve dados públicos do utilizador (opcional)
    utilizador = serializers.StringRelatedField(read_only=True)

    # recebe apenas o ID quando criar/editar
    utilizador_id = serializers.PrimaryKeyRelatedField(
        queryset=Utilizador.objects.all(),
        source='utilizador',           # mapeia para o FK real
        write_only=True
    )

    ficheiro_url = serializers.SerializerMethodField()

    class Meta:
        model  = Galeria
        fields = [
            'id', 'titulo', 'descricao',
            'ficheiro', 'ficheiro_url',
            'utilizador', 'utilizador_id',   # ← ambos
            'data', 'status','likes', 'comentarios'
        ]

    def get_ficheiro_url(self, obj):
        req = self.context.get('request')
        return req.build_absolute_uri(obj.ficheiro.url) if obj.ficheiro else None