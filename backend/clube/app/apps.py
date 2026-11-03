from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        # ficheiros substituídos/apagados vão para a fila de limpeza; vídeos são otimizados
        from . import signals, uploads
        signals.ligar_limpeza_ao_apagar()
        uploads.ligar()   # só imagens/vídeos (e com tamanho máximo) em todos os uploads públicos
        # comprovativos por email quando um pagamento é aprovado (encomendas e mensalidades)
        from .utils import emails_fiscais
        emails_fiscais.ligar()
        # registo das transações (só de acrescentar): pagamentos, reembolsos, marcações, faturas
        from .utils import registo
        registo.ligar()
        # documentos legais das lojas: apagar a linha apaga o ficheiro privado
        from .utils import documentos_loja  # noqa: F401
        # barra de pesquisa: o índice acompanha produtos, lojas e serviços
        from .utils import pesquisa
        pesquisa.ligar_sinais()
        # encomendas e entregas em tempo real (perfil do cliente, backoffice, condutor)
        from .utils import tempo_real_encomendas
        tempo_real_encomendas.ligar()
        from .utils import tempo_real_subscricoes
        tempo_real_subscricoes.ligar()
        from .utils import tempo_real_faturacao
        tempo_real_faturacao.ligar()
