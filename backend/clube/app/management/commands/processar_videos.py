"""
Worker em segundo plano: otimização de vídeos (app/utils/video.py) e limpeza de ficheiros
apagados/substituídos do storage (app/utils/limpeza.py).

  python manage.py processar_videos                 # fica a correr e processa a fila
  python manage.py processar_videos --uma-vez       # processa o que houver e sai
  python manage.py processar_videos --existentes    # agenda vídeos antigos ainda não otimizados
  python manage.py processar_videos --reprocessar-erros

Corre um só worker por ambiente (dev: serviço `worker` no docker-compose).
"""
import signal
import time

from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.db.utils import OperationalError, ProgrammingError

from app.models import ConversaoVideo, Galeria, Loja, Produto
from app.utils import limpeza, video


class Command(BaseCommand):
    help = 'Processa a fila de otimização de vídeos.'

    def add_arguments(self, parser):
        parser.add_argument('--uma-vez', action='store_true', help='Processa a fila e sai.')
        parser.add_argument('--existentes', action='store_true',
                            help='Agenda vídeos já gravados que ainda não foram otimizados.')
        parser.add_argument('--reprocessar-erros', action='store_true',
                            help='Volta a pôr na fila os vídeos que falharam.')
        parser.add_argument('--intervalo', type=float, default=3.0,
                            help='Segundos entre verificações quando a fila está vazia.')

    def handle(self, *args, **opts):
        self.parar = False
        signal.signal(signal.SIGTERM, self._sinal)
        signal.signal(signal.SIGINT, self._sinal)

        if opts['existentes'] or opts['reprocessar_erros']:
            n = self._agendar_existentes(so_erros=opts['reprocessar_erros'] and not opts['existentes'])
            self.stdout.write(f'{n} vídeo(s) agendado(s).')
            if not opts['uma_vez']:
                return

        self._esperar_bd()
        n = video.recuperar_interrompidas()
        if n:
            self.stdout.write(f'{n} tarefa(s) interrompida(s) de volta à fila.')

        self.stdout.write(self.style.SUCCESS('Worker de vídeo e limpeza a correr.'))
        while not self.parar:
            close_old_connections()
            try:
                apagados = limpeza.processar_lote()
                t = video.proxima_tarefa()
            except (OperationalError, ProgrammingError) as e:
                self.stderr.write(f'BD indisponível: {e}')
                time.sleep(5)
                continue

            if apagados:
                self.stdout.write(f'  limpeza: {apagados} ficheiro(s) tratados')
            if t is None:
                if apagados:
                    continue            # ainda pode haver mais na fila de limpeza
                if opts['uma_vez']:
                    break
                time.sleep(opts['intervalo'])
                continue

            self.stdout.write(f'→ {t}')
            t = video.processar(t)
            mb = lambda b: f'{(b or 0) / 1e6:.1f} MB'
            if t.estado == 'pronto':
                self.stdout.write(self.style.SUCCESS(
                    f'  ✓ {mb(t.bytes_origem)} → {mb(t.bytes_final)} em {t.duracao_s}s'))
            else:
                self.stdout.write(f'  {t.estado}: {t.erro[-300:] if t.erro else ""}')

        self.stdout.write('Worker de vídeo parado.')

    def _sinal(self, *_):
        # termina a conversão em curso e sai
        self.parar = True

    def _esperar_bd(self):
        """No arranque a BD (ou as migrações) podem ainda não estar prontas."""
        while not self.parar:
            try:
                ConversaoVideo.objects.exists()
                return
            except (OperationalError, ProgrammingError):
                close_old_connections()
                self.stdout.write('À espera da base de dados/migrações…')
                time.sleep(3)

    def _agendar_existentes(self, so_erros=False):
        n = 0
        for Modelo, campo in ((Loja, 'banner'), (Produto, 'ficheiro'), (Galeria, 'ficheiro')):
            filtro = {f'{campo}_estado': 'erro'} if so_erros else {f'{campo}_estado__in': ['', 'erro']}
            for obj in Modelo.objects.filter(**filtro).exclude(**{campo: ''}).exclude(**{f'{campo}__isnull': True}):
                if video.reprocessar(obj, campo):
                    n += 1
        return n
