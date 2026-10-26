"""manage.py backup_bd — faz já um backup completo da base de dados (utils/backups.py)."""
from django.core.management.base import BaseCommand, CommandError

from app.utils import backups


class Command(BaseCommand):
    help = 'Backup completo da base de dados para o armazenamento de backups (R2 privado ou BACKUP_DIR).'

    def add_arguments(self, parser):
        parser.add_argument('--automatico', action='store_true', help='conta como o backup automático do dia')

    def handle(self, *args, **opts):
        try:
            b = backups.fazer_backup('automatico' if opts['automatico'] else 'manual')
        except backups.BackupEmCurso as e:
            raise CommandError(str(e))
        if b.estado != 'ok':
            raise CommandError(f'O backup falhou: {b.erro}')
        self.stdout.write(self.style.SUCCESS(f'{b.chave} ({b.tamanho / 1e6:.1f} MB em {b.duracao_s}s)'))
