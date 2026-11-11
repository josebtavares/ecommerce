from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        # ficheiros substituídos/apagados vão para a fila de limpeza; vídeos são otimizados
        from . import signals, uploads
        signals.ligar_limpeza_ao_apagar()
        signals.ligar_password_alterada()   # data da última password (3DS do vinti4)
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
        from .utils import tempo_real_pos              # POS: mesas, contas, turnos, equipa… (ws/pos/)
        tempo_real_pos.ligar()
        from .utils import tempo_real_painel
        tempo_real_painel.ligar()
        from .utils import tempo_real_listas            # produtos, inventário e as listas do admin
        tempo_real_listas.ligar()
        # cache pública da borda (clube/borda.py): o que a loja muda aparece logo aos visitantes
        from .utils import cache_publico
        cache_publico.ligar()
        # vinti4 em produção com os endereços de teste da SISP → erro no arranque (pagamentos/vinti4.py)
        from django.core.checks import register
        from .pagamentos.vinti4 import verificar_configuracao
        register(verificar_configuracao, 'bendi')
