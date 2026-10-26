"""
Varrimento de ficheiros órfãos no storage (rede de segurança da limpeza automática).

  python manage.py limpar_orfaos                    # só mostra (não apaga nada)
  python manage.py limpar_orfaos --apagar           # põe os órfãos na fila de limpeza
  python manage.py limpar_orfaos --dias 30          # só ficheiros com mais de 30 dias (default 7)

Um ficheiro é órfão se nenhum FileField/ImageField de nenhum modelo o referir. Ficheiros
recentes são ignorados (podem ser uploads em curso). Funciona igual no disco (dev) e no R2
(prod) — no R2 listar o bucket custa operações, por isso não convém correr muito amiúde
(ex.: semanalmente). O apagar em si é feito pelo worker, que volta a confirmar que o ficheiro
continua sem uso.
"""
from datetime import timedelta

from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.utils import timezone

from app.utils import limpeza, versoes_media


class Command(BaseCommand):
    help = 'Encontra (e opcionalmente agenda a limpeza de) ficheiros órfãos no storage.'

    def add_arguments(self, parser):
        parser.add_argument('--apagar', action='store_true', help='Agenda a limpeza dos órfãos.')
        parser.add_argument('--dias', type=int, default=7, help='Idade mínima dos ficheiros (dias).')

    def handle(self, *args, **opts):
        usados = set()
        for Modelo, campo in limpeza.campos_ficheiro():
            usados.update(n for n in Modelo.objects.exclude(**{campo: ''})
                          .exclude(**{f'{campo}__isnull': True})
                          .values_list(campo, flat=True).iterator() if n)
        limite = timezone.now() - timedelta(days=opts['dias'])

        orfaos, total_bytes = [], 0
        for nome in self._listar(''):
            if nome in usados or limpeza.protegido(nome):
                continue
            if versoes_media.principal_de(nome) in usados:     # versão leve de um ficheiro em uso
                continue
            try:
                if default_storage.get_modified_time(nome) > limite:
                    continue
                tamanho = default_storage.size(nome)
            except Exception:
                tamanho = 0
            orfaos.append(nome)
            total_bytes += tamanho

        for nome in orfaos:
            self.stdout.write(f'  {nome}')
        self.stdout.write(f'{len(orfaos)} ficheiro(s) órfão(s), {total_bytes / 1e6:.1f} MB '
                          f'(com mais de {opts["dias"]} dias).')

        if opts['apagar'] and orfaos:
            limpeza.agendar_apagar(orfaos, 'varrimento')
            self.stdout.write(self.style.SUCCESS('Agendados para limpeza — o worker apaga-os em segundo plano.'))
        elif orfaos:
            self.stdout.write('Nada foi apagado. Usa --apagar para os pôr na fila de limpeza.')

    def _listar(self, pasta):
        pastas, ficheiros = default_storage.listdir(pasta)
        for f in ficheiros:
            yield f'{pasta}/{f}' if pasta else f
        for p in pastas:
            yield from self._listar(f'{pasta}/{p}' if pasta else p)
