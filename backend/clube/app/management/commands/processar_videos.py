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
from app.utils import horarios, limpeza, repor_backup, subscricoes, video


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
            if repor_backup.em_manutencao():      # a base está a ser reposta: não tocar em nada
                time.sleep(5)
                continue
            close_old_connections()
            self._avisos_horario()
            self._ciclo_subscricoes()
            self._limpar_sessoes()
            self._backup_diario()
            self._exportacoes()
            self._ensaio_reposicao()
            self._copia_media()
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

    def _ciclo_subscricoes(self):
        """A cada 10 minutos: faturas, avisos, pagamento automático e suspensões (utils/subscricoes.py)."""
        if time.monotonic() - getattr(self, '_ultimo_ciclo', -1e9) < 600:
            return
        self._ultimo_ciclo = time.monotonic()
        try:
            from app.utils import subscricoes_pos
            n = subscricoes_pos.garantir_todos()        # POS de antes das subscrições → mês grátis
            if n:
                self.stdout.write(f'  subscrições: {n} POS com o mês grátis')
            r = subscricoes.processar()
            if any(r.values()):
                self.stdout.write(f'  subscrições: {r}')
        except Exception as e:          # um erro aqui não pode parar os vídeos
            self.stderr.write(f'  subscrições: ciclo falhou: {e}')

    def _backup_diario(self):
        """De 5 em 5 minutos vê se já é hora do backup da base de dados (utils/backups.py)."""
        if time.monotonic() - getattr(self, '_ultima_verificacao_backup', -1e9) < 300:
            return
        self._ultima_verificacao_backup = time.monotonic()
        try:
            from app.utils import backups
            if not backups.backup_devido():
                return
            b = backups.fazer_backup('automatico')
            if b.estado == 'ok':
                self.stdout.write(self.style.SUCCESS(f'  backup: {b.chave} ({b.tamanho / 1e6:.1f} MB em {b.duracao_s}s)'))
            else:
                self.stderr.write(f'  backup: falhou: {b.erro[-300:]}')
        except Exception as e:          # um erro aqui não pode parar os vídeos
            self.stderr.write(f'  backup: {e}')

    def _exportacoes(self):
        """De 10 em 10 segundos: gera a próxima exportação de dados de loja pedida; de hora a hora apaga as
        que passaram do prazo (utils/exportacao_loja.py)."""
        if time.monotonic() - getattr(self, '_ultima_exportacao', -1e9) < 10:
            return
        self._ultima_exportacao = time.monotonic()
        try:
            from app.utils import exportacao_loja
            if time.monotonic() - getattr(self, '_ultima_expiracao', -1e9) >= 3600:
                self._ultima_expiracao = time.monotonic()
                exportacao_loja.expirar()
            if exportacao_loja.processar_fila():
                self.stdout.write('  exportação de loja gerada')
        except Exception as e:          # um erro aqui não pode parar os vídeos
            self.stderr.write(f'  exportação: {e}')

    def _ensaio_reposicao(self):
        """De 10 em 10 segundos: o ensaio de reposição pedido no admin, ou o periódico quando é devido
        (utils/backups.ensaiar_reposicao — repõe numa base temporária, nunca na da plataforma)."""
        if time.monotonic() - getattr(self, '_ultimo_ensaio', -1e9) < 10:
            return
        self._ultimo_ensaio = time.monotonic()
        try:
            from app.utils import backups
            b = backups.processar_ensaio()
            if b is not None:
                d = b.ensaio_detalhe
                if b.ensaio_ok:
                    self.stdout.write(self.style.SUCCESS(
                        f"  ensaio de reposição: {d.get('backup')} ok ({d.get('tabelas')} tabelas, {d.get('total_s')}s)"))
                else:
                    self.stderr.write(f"  ensaio de reposição: falhou: {d.get('erro', '')[-300:]}")
        except Exception as e:          # um erro aqui não pode parar os vídeos
            self.stderr.write(f'  ensaio de reposição: {e}')

    def _copia_media(self):
        """De 10 em 10 segundos: a cópia das fotos e vídeos pedida no admin; de 5 em 5 minutos vê se é hora
        da diária (utils/backup_media.py — incremental, só transfere o que é novo)."""
        if time.monotonic() - getattr(self, '_ultima_copia_media', -1e9) < 10:
            return
        self._ultima_copia_media = time.monotonic()
        verificar = time.monotonic() - getattr(self, '_ultima_verificacao_media', -1e9) >= 300
        if verificar:
            self._ultima_verificacao_media = time.monotonic()
        try:
            from app.utils import backup_media
            c = backup_media.processar(verificar_devida=verificar)
            if c is not None:
                if c.estado == 'ok':
                    self.stdout.write(self.style.SUCCESS(
                        f'  cópia media: {c.copiados} copiados ({c.bytes_copiados / 1e6:.1f} MB), '
                        f'{c.guardados_apagados} apagados guardados, {c.ficheiros} na cópia ({c.duracao_s}s)'))
                else:
                    self.stderr.write(f'  cópia media: falhou: {c.erro[-300:]}')
        except Exception as e:          # um erro aqui não pode parar os vídeos
            self.stderr.write(f'  cópia media: {e}')

    def _limpar_sessoes(self):
        """Uma vez por dia: apaga os tokens de sessão já expirados (lista negra do logout)."""
        if time.monotonic() - getattr(self, '_ultima_limpeza_sessoes', -1e9) < 86400:
            return
        self._ultima_limpeza_sessoes = time.monotonic()
        try:
            from django.core.management import call_command
            call_command('flushexpiredtokens', verbosity=0)
        except Exception as e:          # um erro aqui não pode parar os vídeos
            self.stderr.write(f'  sessões: limpeza falhou: {e}')

    def _avisos_horario(self):
        """Uma vez por minuto: avisa as lojas das encomendas agendadas para hoje (utils/horarios.py) e cancela
        as encomendas por pagar fora do prazo (utils/encomendas.py)."""
        if time.monotonic() - getattr(self, '_ultimo_aviso', -1e9) < 60:
            return
        self._ultimo_aviso = time.monotonic()
        try:
            n = horarios.avisar_agendadas()
            if n:
                self.stdout.write(f'  horários: {n} loja(s) avisada(s) das encomendas agendadas para hoje')
        except Exception as e:          # um erro aqui não pode parar os vídeos
            self.stderr.write(f'  horários: aviso falhou: {e}')
        try:
            from app.utils.encomendas import expirar_por_pagar
            n = expirar_por_pagar()
            if n:
                self.stdout.write(f'  encomendas: {n} por pagar fora do prazo cancelada(s) (stock reposto)')
        except Exception as e:
            self.stderr.write(f'  encomendas: expirar falhou: {e}')
        try:
            from app.servicos.ciclo import processar as ciclo_marcacoes
            r = ciclo_marcacoes()
            if any(r.values()):
                self.stdout.write(f'  marcações: {r}')
        except Exception as e:
            self.stderr.write(f'  marcações: ciclo falhou: {e}')
        try:
            from app.utils.devolucoes import escalar_sem_resposta
            n = escalar_sem_resposta()
            if n:
                self.stdout.write(f'  devoluções: {n} pedido(s) sem resposta da loja enviado(s) à Bendi')
        except Exception as e:
            self.stderr.write(f'  devoluções: escalar falhou: {e}')
        try:
            # reembolsos que o fornecedor recusou: nova tentativa quando a espera acaba (utils/devolucoes.py)
            from app.utils.devolucoes import reembolsos_por_concluir
            from app.servicos.marcacoes import reembolsos_por_concluir as marcacoes_por_concluir
            n, m = reembolsos_por_concluir(), marcacoes_por_concluir()
            if n or m:
                self.stdout.write(f'  reembolsos: {n} encomenda(s) e {m} marcação(ões) tentada(s) de novo')
        except Exception as e:
            self.stderr.write(f'  reembolsos: nova tentativa falhou: {e}')
        try:
            # suspensões que acabaram (as lojas suspensas com a conta voltam a horas) e contas
            # cujo prazo para apagar acabou (utils/moderacao.py, utils/eliminacao.py)
            from app.utils.moderacao import levantar_expiradas
            from app.utils.eliminacao import eliminar_vencidas
            n, m = levantar_expiradas(), eliminar_vencidas()
            if n or m:
                self.stdout.write(f'  contas: {n} suspensão(ões) terminada(s), {m} conta(s) apagada(s)')
        except Exception as e:
            self.stderr.write(f'  contas: falhou: {e}')
        # documentos das lojas a expirar ou expirados (utils/documentos_loja.py) — de hora a hora chega
        if time.monotonic() - getattr(self, '_ultimo_documentos', -1e9) >= 3600:
            self._ultimo_documentos = time.monotonic()
            try:
                from app.utils.documentos_loja import avisar_validades
                n = avisar_validades()
                if n:
                    self.stdout.write(f'  documentos: {n} aviso(s) de validade')
            except Exception as e:
                self.stderr.write(f'  documentos: avisos falharam: {e}')

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
