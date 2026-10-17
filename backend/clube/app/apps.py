from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        # ficheiros substituídos/apagados vão para a fila de limpeza; vídeos são otimizados
        from . import signals, uploads
        signals.ligar_limpeza_ao_apagar()
        uploads.ligar()   # só imagens/vídeos (e com tamanho máximo) em todos os uploads públicos
