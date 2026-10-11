from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        # ficheiros substituídos/apagados vão para a fila de limpeza; vídeos são otimizados
        from . import signals
        signals.ligar_limpeza_ao_apagar()
