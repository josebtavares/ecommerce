from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Refaz o índice da barra de pesquisa (utils/pesquisa.py).'

    def handle(self, *args, **opts):
        from app.utils.pesquisa import reindexar_tudo
        self.stdout.write(f'{reindexar_tudo()} entradas no índice.')
