"""manage.py backup_bd — faz já um backup completo da base de dados (utils/backups.py).

  manage.py backup_bd                 backup manual
  manage.py backup_bd --automatico    conta como o backup automático do dia
  manage.py backup_bd --ensaiar [ID]  ensaio de reposição (o mais recente, ou o backup ID) numa base temporária
  manage.py backup_bd --assinar       assina os backups guardados que ainda não têm assinatura
"""
from django.core.management.base import BaseCommand, CommandError

from app.models import BackupBD
from app.utils import backups


class Command(BaseCommand):
    help = 'Backup completo da base de dados para o armazenamento de backups (R2 privado ou BACKUP_DIR).'

    def add_arguments(self, parser):
        parser.add_argument('--automatico', action='store_true', help='conta como o backup automático do dia')
        parser.add_argument('--ensaiar', nargs='?', const=0, type=int, metavar='ID',
                            help='repõe um backup numa base temporária e confere-o (sem ID: o mais recente)')
        parser.add_argument('--assinar', action='store_true', help='assina os backups que ainda não têm assinatura')

    def handle(self, *args, **opts):
        if opts['assinar']:
            n = backups.assinar_existentes()
            return self.stdout.write(self.style.SUCCESS(f'{n} backup(s) assinados.'))
        if opts['ensaiar'] is not None:
            return self._ensaiar(opts['ensaiar'])
        try:
            b = backups.fazer_backup('automatico' if opts['automatico'] else 'manual')
        except backups.BackupEmCurso as e:
            raise CommandError(str(e))
        if b.estado != 'ok':
            raise CommandError(f'O backup falhou: {b.erro}')
        self.stdout.write(self.style.SUCCESS(f'{b.chave} ({b.tamanho / 1e6:.1f} MB em {b.duracao_s}s)'))

    def _ensaiar(self, backup_id):
        b = BackupBD.objects.filter(pk=backup_id).first() if backup_id else None
        if backup_id and not b:
            raise CommandError(f'Não há o backup {backup_id}.')
        try:
            b = backups.ensaiar_reposicao(b)
        except (backups.EnsaioEmCurso, ValueError) as e:
            raise CommandError(str(e))
        d = b.ensaio_detalhe
        if not b.ensaio_ok:
            raise CommandError(f"O ensaio falhou: {d.get('erro')}")
        self.stdout.write(self.style.SUCCESS(
            f"{d['backup']}: reposto e conferido — {d['tabelas']} tabelas, {d['linhas']} linhas, "
            f"{d['utilizadores']} utilizadores, {d['lojas']} lojas, migração {d['ultima_migracao']} "
            f"(descarregar {d['descarregar_s']}s, repor {d['repor_s']}s, total {d['total_s']}s)"))
