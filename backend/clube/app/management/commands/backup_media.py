"""manage.py backup_media — cópia das fotos e vídeos para o armazenamento de backups (utils/backup_media.py).

  manage.py backup_media                                   copia já o que é novo (manual)
  manage.py backup_media --repor publico                   SIMULA: diz o que falta no storage das lojas
  manage.py backup_media --repor publico --confirmar       repõe-o (só ficheiros em falta, nunca substitui)
  manage.py backup_media --repor publico --dia 20261026    a partir dos apagados guardados nesse dia
  manage.py backup_media --repor publico --prefixo lojas/7/ só uma pasta
"""
from django.core.management.base import BaseCommand, CommandError

from app.utils import backup_media


class Command(BaseCommand):
    help = 'Cópia incremental das fotos e vídeos para o armazenamento de backups; --repor devolve-os.'

    def add_arguments(self, parser):
        parser.add_argument('--repor', metavar='ORIGEM', choices=('publico', 'privado'))
        parser.add_argument('--dia', metavar='AAAAMMDD', help='repor a partir de media-apagados/AAAAMMDD/')
        parser.add_argument('--prefixo', default='', help='só os ficheiros cujo caminho começa por isto')
        parser.add_argument('--confirmar', action='store_true', help='sem isto, --repor só simula')

    def handle(self, *args, **opts):
        if opts['repor']:
            return self._repor(opts)
        try:
            c = backup_media.copiar('manual')
        except backup_media.CopiaEmCurso as e:
            raise CommandError(str(e))
        if c.estado != 'ok':
            raise CommandError(f'A cópia falhou: {c.erro}')
        self.stdout.write(self.style.SUCCESS(
            f'{c.copiados} copiados ({c.bytes_copiados / 1e6:.1f} MB), {c.guardados_apagados} apagados guardados, '
            f'{c.purgados} removidos de vez; na cópia: {c.ficheiros} ficheiros, {c.bytes / 1e6:.1f} MB ({c.duracao_s}s)'))

    def _repor(self, opts):
        r = backup_media.repor(opts['repor'], opts['dia'], opts['prefixo'], simular=not opts['confirmar'])
        verbo = 'repostos' if opts['confirmar'] else 'a repor (simulação — junta --confirmar)'
        self.stdout.write(f"{r['repostos']} {verbo}, {r['bytes'] / 1e6:.1f} MB; {r['ja_existiam']} já existiam")
        for f in r['falhas']:
            self.stderr.write(f'  falhou: {f}')
        if r['falhas']:
            raise CommandError(f"{len(r['falhas'])} ficheiro(s) não foram repostos")
