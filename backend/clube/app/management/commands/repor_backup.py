"""manage.py repor_backup — repõe a base de dados a partir de um backup assinado (utils/repor_backup.py).

Normalmente corre-se pelo script scripts/repor_backup.py (--dev ou --prod), que trata das ligações.

  manage.py repor_backup --alvo dev --listar
  manage.py repor_backup --alvo dev                         escolhe na lista e pede confirmação
  manage.py repor_backup --alvo prod --backup bende-20261026-030512-automatico.dump
"""
import getpass
import socket

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from app.utils import backups, repor_backup


class Command(BaseCommand):
    help = 'Repõe a base de dados a partir de um backup do armazenamento de backups (só backups assinados).'

    def add_arguments(self, parser):
        parser.add_argument('--alvo', choices=('dev', 'prod'), required=True)
        parser.add_argument('--listar', action='store_true', help='só mostra os backups que há')
        parser.add_argument('--backup', metavar='NOME', help='nome do ficheiro (sem isto, escolhe-se na lista)')
        parser.add_argument('--confirmar', metavar='FRASE', help='a frase de confirmação (para correr sem perguntas)')
        parser.add_argument('--sem-copia-atual', action='store_true',
                            help='continua mesmo que não consiga guardar o estado atual (base estragada)')
        parser.add_argument('--quem', default='', help='quem está a repor (vai no email de aviso)')

    def handle(self, *args, **o):
        try:
            lista = repor_backup.disponiveis()
        except Exception as e:
            raise CommandError(f'Não consegui ler o armazenamento de backups: {e}')
        if not lista:
            raise CommandError('Não há nenhum backup no armazenamento de backups.')
        if o['listar'] or not o['backup']:
            self._listar(lista)
        if o['listar']:
            return
        nome = o['backup']
        if not nome:
            escolha = input('\nNúmero do backup a repor (Enter = 1, o mais recente; q = sair): ').strip().lower()
            if escolha == 'q':
                return
            try:
                nome = lista[int(escolha or 1) - 1]['nome']
            except (ValueError, IndexError):
                raise CommandError('Escolha inválida.')
        quem = o['quem'] or f'{getpass.getuser()}@{socket.gethostname()}'
        try:
            repor_backup.executar(o['alvo'], nome, o['confirmar'], o['sem_copia_atual'], quem,
                                  escrever=self.stdout.write)
        except repor_backup.Recusado as e:
            raise CommandError(str(e))
        except RuntimeError as e:
            raise CommandError(str(e))
        self.stdout.write(self.style.SUCCESS('Base reposta.'))

    def _listar(self, lista):
        arm = backups.armazenamento()
        self.stdout.write('\nBackups no armazenamento (do mais recente para o mais antigo):')
        for i, b in enumerate(lista[:30], 1):
            assinado = 'assinado' if arm.assinatura(b['chave']) else 'SEM ASSINATURA (recusado)'
            self.stdout.write(f'  {i:>2}. {b["nome"]:52} {timezone.localtime(b["quando"]):%d/%m/%Y %H:%M}  '
                              f'{b["tamanho"] / 1e6:6.1f} MB  {assinado}')
        if len(lista) > 30:
            self.stdout.write(f'  … e mais {len(lista) - 30} (usa --backup NOME)')
