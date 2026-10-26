"""
Backups completos da base de dados, guardados fora do Railway (o plano Hobby não tem backups).

  fazer_backup(tipo, user)  → pg_dump -Fc, confirma que o ficheiro se lê (pg_restore -l), envia-o
                              para o armazenamento e aplica a retenção. Devolve o BackupBD.
  backup_devido(agora)      → o worker (manage.py processar_videos) chama de minutos a minutos:
                              True quando já passou a hora do backup de hoje e ainda não há um.

Um único ficheiro com tudo: os dados estão ligados entre si (encomendas → clientes, lojas,
produtos...), por isso só se repõe a base inteira — numa base de ensaio primeiro, nunca por botão.

Armazenamento: bucket R2 PRIVADO só para backups (settings.BACKUP_R2_*); sem ele (dev), a pasta
settings.BACKUP_DIR. As fotos e vídeos já vivem no R2 e não entram aqui.

Retenção dos automáticos: o último de cada um dos últimos 7 dias, de cada uma das últimas 4 semanas
e de cada um dos últimos 12 meses. Os manuais ficam 30 dias.
"""
import logging
import os
import shutil
import subprocess
import tempfile
import time
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.db import connection
from django.utils import timezone

from ..models import BackupBD

log = logging.getLogger(__name__)

TRANCA = 'backup_bd:a_correr'
LIMITE_S = 30 * 60                 # um pg_dump que demore mais do que isto está encravado
DIAS_MANUAIS = 30
TENTATIVAS_POR_DIA = 3
INTERVALO_TENTATIVAS = timedelta(minutes=30)


class BackupEmCurso(Exception):
    pass


# ── armazenamento ──────────────────────────────────────────────────

class _Disco:
    def __init__(self):
        self.raiz = Path(settings.BACKUP_DIR)

    def guardar(self, origem, chave):
        destino = self.raiz / chave
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(origem, destino)

    def apagar(self, chave):
        (self.raiz / chave).unlink(missing_ok=True)

    def existe(self, chave):
        return (self.raiz / chave).exists()

    def caminho(self, chave):
        return self.raiz / chave

    def descarregar(self, chave, destino):
        shutil.copyfile(self.raiz / chave, destino)

    def url(self, chave, segundos):
        return None             # na dev o ficheiro sai por uma view com link assinado (Views/backupView.py)

    # usados pela cópia das fotos e vídeos (utils/backup_media.py)
    def listar(self, prefixo=''):
        """{chave: (tamanho, mtime em segundos)} de tudo o que começa por prefixo."""
        res = {}
        base = self.raiz / prefixo if prefixo else self.raiz
        if not base.exists():
            return res
        for p in base.rglob('*'):
            if p.is_file():
                st = p.stat()
                res[p.relative_to(self.raiz).as_posix()] = (st.st_size, st.st_mtime)
        return res

    def guardar_obj(self, fobj, chave, tipo=None):
        destino = self.raiz / chave
        destino.parent.mkdir(parents=True, exist_ok=True)
        with open(destino, 'wb') as f:
            shutil.copyfileobj(fobj, f, 1024 * 1024)

    def abrir(self, chave):
        return open(self.raiz / chave, 'rb'), None

    def mover(self, de, para):
        destino = self.raiz / para
        destino.parent.mkdir(parents=True, exist_ok=True)
        os.replace(self.raiz / de, destino)


class _R2:
    def __init__(self):
        import boto3
        from botocore.config import Config
        self.bucket = settings.BACKUP_R2_BUCKET
        self.s3 = boto3.client(
            's3', endpoint_url=settings.BACKUP_R2_ENDPOINT_URL,
            aws_access_key_id=settings.BACKUP_R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.BACKUP_R2_SECRET_ACCESS_KEY,
            region_name='auto', config=Config(signature_version='s3v4', retries={'max_attempts': 5}))

    def guardar(self, origem, chave):
        self.s3.upload_file(str(origem), self.bucket, chave, ExtraArgs={'ContentType': 'application/octet-stream'})

    def apagar(self, chave):
        self.s3.delete_object(Bucket=self.bucket, Key=chave)

    def existe(self, chave):
        try:
            self.s3.head_object(Bucket=self.bucket, Key=chave)
            return True
        except Exception:
            return False

    def caminho(self, chave):
        return None

    def descarregar(self, chave, destino):
        self.s3.download_file(self.bucket, chave, str(destino))

    def url(self, chave, segundos):
        """Link temporário direto ao bucket privado (expira; não passa pelo servidor)."""
        return self.s3.generate_presigned_url('get_object', ExpiresIn=segundos, Params={
            'Bucket': self.bucket, 'Key': chave,
            'ResponseContentDisposition': f'attachment; filename="{chave.rsplit("/", 1)[-1]}"'})

    def listar(self, prefixo=''):
        res = {}
        for pagina in self.s3.get_paginator('list_objects_v2').paginate(Bucket=self.bucket, Prefix=prefixo):
            for o in pagina.get('Contents', []):
                res[o['Key']] = (o['Size'], o['LastModified'].timestamp())
        return res

    def guardar_obj(self, fobj, chave, tipo=None):
        self.s3.upload_fileobj(fobj, self.bucket, chave,
                               ExtraArgs={'ContentType': tipo or 'application/octet-stream'})

    def abrir(self, chave):
        r = self.s3.get_object(Bucket=self.bucket, Key=chave)
        return r['Body'], r.get('ContentType')

    def mover(self, de, para):
        self.s3.copy_object(Bucket=self.bucket, Key=para, CopySource={'Bucket': self.bucket, 'Key': de})
        self.s3.delete_object(Bucket=self.bucket, Key=de)


def armazenamento():
    return _R2() if settings.BACKUP_R2_BUCKET else _Disco()


# ── pg_dump ────────────────────────────────────────────────────────

def _ambiente_pg():
    bd = connection.settings_dict
    env = {**os.environ, 'PGPASSWORD': str(bd.get('PASSWORD') or '')}
    ssl = (bd.get('OPTIONS') or {}).get('sslmode')
    if ssl:
        env['PGSSLMODE'] = ssl
    args = ['-h', str(bd.get('HOST') or 'localhost'), '-p', str(bd.get('PORT') or 5432),
            '-U', str(bd.get('USER') or ''), '-d', str(bd.get('NAME') or '')]
    return args, env


def _dump(destino):
    args, env = _ambiente_pg()
    r = subprocess.run(['pg_dump', '-Fc', '--no-owner', '--no-acl', *args, '-f', str(destino)],
                       env=env, capture_output=True, text=True, timeout=LIMITE_S)
    if r.returncode != 0:
        raise RuntimeError(f'pg_dump falhou: {r.stderr.strip()[-800:]}')
    # um backup que não se consegue ler não é um backup
    r = subprocess.run(['pg_restore', '-l', str(destino)], capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(f'o ficheiro do backup não se lê: {r.stderr.strip()[-800:]}')
    tabelas = sum(1 for linha in r.stdout.splitlines() if ' TABLE DATA ' in linha)
    if not tabelas:
        raise RuntimeError('o backup não tem dados de nenhuma tabela')
    return tabelas


# ── backup ─────────────────────────────────────────────────────────

def destinatarios_alertas():
    """Super-admins do painel (role superadmin) e superusers do Django, com email."""
    from django.db.models import Q
    return sorted(set(User.objects.filter(is_active=True).filter(
        Q(is_superuser=True) | Q(is_staff=True, utilizador__role_admin='superadmin')
    ).exclude(email='').values_list('email', flat=True)))


def _avisar_falha(b):
    para = destinatarios_alertas()
    if not para:
        return
    seguinte = ('O worker volta a tentar daqui a 30 minutos (até 3 vezes por dia).' if b.tipo == 'automatico'
                else 'Podes tentar outra vez no painel de admin.')
    try:
        EmailMessage(
            subject='Bende: o backup da base de dados falhou',
            body=(f'O backup {b.get_tipo_display().lower()} de {timezone.localtime(b.criado_em):%d/%m/%Y %H:%M} falhou.\n\n'
                  f'Erro: {b.erro[-1500:]}\n\n{seguinte} Se continuar a falhar, '
                  'a plataforma fica sem cópia de segurança recente.\n\nBende'),
            from_email=settings.DEFAULT_FROM_EMAIL, to=para,
        ).send()
    except Exception:
        log.exception('backup: não consegui enviar o aviso de falha')


def _encravados():
    """Um backup 'a correr' há mais de 2 h morreu com o processo (deploy, reinício)."""
    BackupBD.objects.filter(estado='a_correr', criado_em__lt=timezone.now() - timedelta(hours=2)).update(
        estado='erro', erro='Interrompido (o processo parou a meio).')


def fazer_backup(tipo='automatico', user=None):
    if not cache.add(TRANCA, 1, LIMITE_S + 600):
        raise BackupEmCurso('Já há um backup a correr.')
    _encravados()
    b = BackupBD.objects.create(tipo=tipo, pedido_por=user)
    inicio = time.monotonic()
    pasta = tempfile.mkdtemp(prefix='backup-')
    try:
        local = timezone.localtime(b.criado_em)
        nome = f'bende-{local:%Y%m%d-%H%M%S}-{tipo}.dump'
        ficheiro = Path(pasta) / nome
        _dump(ficheiro)
        chave = f'bd/{local:%Y}/{local:%m}/{nome}'
        armazenamento().guardar(ficheiro, chave)
        b.chave, b.tamanho, b.estado = chave, ficheiro.stat().st_size, 'ok'
    except Exception as e:
        log.exception('backup da base de dados falhou')
        b.estado, b.erro = 'erro', str(e)[:4000]
    finally:
        shutil.rmtree(pasta, ignore_errors=True)
        b.duracao_s = round(time.monotonic() - inicio, 1)
        b.save(update_fields=['chave', 'tamanho', 'estado', 'erro', 'duracao_s'])
        cache.delete(TRANCA)
    if b.estado == 'erro':
        _avisar_falha(b)
    else:
        try:
            aplicar_retencao()
        except Exception:
            log.exception('backup: a retenção falhou (o backup ficou feito)')
    return b


# ── quando fazer ───────────────────────────────────────────────────

def backup_devido(agora=None):
    agora = timezone.localtime(agora or timezone.now())
    if agora.hour < settings.BACKUP_HORA:
        return False
    inicio_dia = agora.replace(hour=0, minute=0, second=0, microsecond=0)
    hoje = BackupBD.objects.filter(tipo='automatico', criado_em__gte=inicio_dia)
    if hoje.filter(estado__in=('ok', 'a_correr')).exists():
        return False
    falhas = hoje.filter(estado='erro')
    if falhas.count() >= TENTATIVAS_POR_DIA:
        return False
    ultima = falhas.order_by('-criado_em').first()
    return not ultima or agora - ultima.criado_em >= INTERVALO_TENTATIVAS


# ── retenção ───────────────────────────────────────────────────────

def a_manter(backups, agora):
    """ids dos automáticos a guardar: o último de cada dia (7), semana (4) e mês (12) mais recentes."""
    hoje = timezone.localtime(agora).date()
    ultimo = {}                     # (período, chave do período) → backup mais recente
    for b in backups:
        d = timezone.localtime(b.criado_em).date()
        for periodo, k in (('dia', d), ('semana', d.isocalendar()[:2]), ('mes', (d.year, d.month))):
            atual = ultimo.get((periodo, k))
            if atual is None or b.criado_em > atual.criado_em:
                ultimo[(periodo, k)] = b
    manter = set()
    semana_atual = hoje - timedelta(days=hoje.weekday())
    for (periodo, k), b in ultimo.items():
        if periodo == 'dia' and (hoje - k).days < 7:
            manter.add(b.id)
        elif periodo == 'semana':
            inicio = timezone.localtime(b.criado_em).date()
            inicio -= timedelta(days=inicio.weekday())
            if (semana_atual - inicio).days < 28:
                manter.add(b.id)
        elif periodo == 'mes' and (hoje.year - k[0]) * 12 + hoje.month - k[1] < 12:
            manter.add(b.id)
    return manter


def aplicar_retencao(agora=None):
    agora = agora or timezone.now()
    vivos = BackupBD.objects.filter(estado='ok', apagado_em__isnull=True)
    automaticos = list(vivos.filter(tipo='automatico'))
    manter = a_manter(automaticos, agora)
    sair = [b for b in automaticos if b.id not in manter]
    sair += list(vivos.filter(tipo='manual', criado_em__lt=agora - timedelta(days=DIAS_MANUAIS)))
    arm = armazenamento()
    for b in sair:
        try:
            if b.chave:
                arm.apagar(b.chave)
            b.apagado_em = agora
            b.save(update_fields=['apagado_em'])
        except Exception:
            log.exception('backup: não consegui apagar %s', b.chave)
    # tentativas falhadas antigas: só ocupam a lista
    BackupBD.objects.filter(estado='erro', criado_em__lt=agora - timedelta(days=DIAS_MANUAIS)).delete()
    return len(sair)


# ── ensaio de reposição ────────────────────────────────────────────
# Um backup só vale se se conseguir repor. De BACKUP_ENSAIO_DIAS em BACKUP_ENSAIO_DIAS (ou a pedido no admin) o
# worker descarrega o backup mais recente, repõe-no numa base TEMPORÁRIA (BD_ENSAIO, nunca a da plataforma),
# confere as tabelas e apaga-a. O procedimento para repor a sério está em docs/REPOR_BACKUP.md.

TRANCA_ENSAIO = 'backup_bd:ensaio'
PEDIDO_ENSAIO = 'backup_bd:ensaio_pedido'      # id do backup pedido no admin (o worker apanha-o)
BD_ENSAIO = 'bende_ensaio_reposicao'
TABELAS_CHAVE = ('auth_user', 'app_utilizador', 'app_loja', 'django_migrations')
SQL_CONTAR = ("SELECT table_name, (xpath('/row/c/text()', query_to_xml(format('SELECT count(*) AS c FROM public.%I', "
              "table_name), false, true, '')))[1]::text FROM information_schema.tables "
              "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY 1")


class EnsaioEmCurso(Exception):
    pass


def _servidor_ensaio():
    """(args de ligação sem -d, env, base onde correr CREATE/DROP DATABASE)."""
    if settings.BACKUP_ENSAIO_URL:
        from urllib.parse import unquote, urlparse
        u = urlparse(settings.BACKUP_ENSAIO_URL)
        env = {**os.environ, 'PGPASSWORD': unquote(u.password or '')}
        args = ['-h', u.hostname or 'localhost', '-p', str(u.port or 5432), '-U', unquote(u.username or '')]
        return args, env, (u.path or '/postgres').lstrip('/') or 'postgres'
    args, env = _ambiente_pg()
    return args[:-2], env, args[-1]


def _psql(args, env, sql, bd):
    r = subprocess.run(['psql', *args, '-d', bd, '-v', 'ON_ERROR_STOP=1', '-Atc', sql],
                       env=env, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[-600:])
    return r.stdout


def pedir_ensaio(backup_id):
    if cache.get(TRANCA_ENSAIO) or cache.get(PEDIDO_ENSAIO):
        raise EnsaioEmCurso('Já há um ensaio de reposição pedido ou a correr.')
    cache.set(PEDIDO_ENSAIO, backup_id, 3600)


def ensaio_em_curso():
    return bool(cache.get(TRANCA_ENSAIO) or cache.get(PEDIDO_ENSAIO))


def ensaio_devido(agora=None):
    """O worker ensaia sozinho se não houver um ensaio bem-sucedido nos últimos BACKUP_ENSAIO_DIAS dias
    (depois do backup diário; se falhar, volta a tentar no dia seguinte)."""
    agora = timezone.localtime(agora or timezone.now())
    if agora.hour < settings.BACKUP_HORA + 1:
        return False
    ensaios = BackupBD.objects.filter(ensaio_em__isnull=False)
    if ensaios.filter(ensaio_ok=True, ensaio_em__gte=agora - timedelta(days=settings.BACKUP_ENSAIO_DIAS)).exists():
        return False
    if ensaios.filter(ensaio_em__gte=agora - timedelta(hours=24)).exists():
        return False
    return BackupBD.objects.filter(estado='ok', apagado_em__isnull=True).exists()


def ultimo_ensaio():
    return BackupBD.objects.filter(ensaio_em__isnull=False).order_by('-ensaio_em').first()


def ensaiar_reposicao(backup=None):
    """Repõe o backup (por omissão o mais recente) numa base temporária e confere-o. Devolve o BackupBD
    com ensaio_ok / ensaio_detalhe preenchidos. Nunca toca na base da plataforma."""
    if not cache.add(TRANCA_ENSAIO, 1, LIMITE_S + 600):
        raise EnsaioEmCurso('Já há um ensaio de reposição a correr.')
    try:
        b = backup or BackupBD.objects.filter(estado='ok', apagado_em__isnull=True).order_by('-criado_em').first()
        if not b or b.estado != 'ok' or b.apagado_em or not b.chave:
            raise ValueError('Não há nenhum backup disponível para ensaiar.')
    except Exception:
        cache.delete(TRANCA_ENSAIO)
        raise
    det, ok = {'backup': b.chave.rsplit('/', 1)[-1]}, False
    inicio = time.monotonic()
    pasta = tempfile.mkdtemp(prefix='ensaio-')
    args, env, manutencao = _servidor_ensaio()
    criada = False
    try:
        if BD_ENSAIO == connection.settings_dict.get('NAME'):
            raise RuntimeError('a base de ensaio não pode ser a da plataforma')
        ficheiro = Path(pasta) / 'backup.dump'
        t = time.monotonic()
        armazenamento().descarregar(b.chave, ficheiro)
        det['descarregar_s'] = round(time.monotonic() - t, 1)
        r = subprocess.run(['pg_restore', '-l', str(ficheiro)], capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            raise RuntimeError(f'o ficheiro não se lê: {r.stderr.strip()[-600:]}')
        no_backup = sum(1 for linha in r.stdout.splitlines() if ' TABLE DATA ' in linha)

        _psql(args, env, f'DROP DATABASE IF EXISTS {BD_ENSAIO} WITH (FORCE)', manutencao)
        _psql(args, env, f'CREATE DATABASE {BD_ENSAIO}', manutencao)
        criada = True
        t = time.monotonic()
        r = subprocess.run(['pg_restore', '--no-owner', '--no-acl', '--exit-on-error', *args, '-d', BD_ENSAIO, str(ficheiro)],
                           env=env, capture_output=True, text=True, timeout=LIMITE_S)
        if r.returncode != 0:
            raise RuntimeError(f'pg_restore falhou: {r.stderr.strip()[-800:]}')
        det['repor_s'] = round(time.monotonic() - t, 1)

        contagens = {}
        for linha in _psql(args, env, SQL_CONTAR, BD_ENSAIO).splitlines():
            if '|' in linha:
                nome, n = linha.split('|', 1)
                contagens[nome] = int(n or 0)
        det.update(tabelas=len(contagens), tabelas_no_backup=no_backup, linhas=sum(contagens.values()),
                   utilizadores=contagens.get('auth_user', 0), lojas=contagens.get('app_loja', 0),
                   encomendas=contagens.get('app_encomenda', 0))
        det['ultima_migracao'] = _psql(args, env, "SELECT name FROM django_migrations WHERE app = 'app' "
                                                  "ORDER BY id DESC LIMIT 1", BD_ENSAIO).strip()
        problemas = []
        if len(contagens) != no_backup:
            problemas.append(f'o backup tem {no_backup} tabelas e só foram repostas {len(contagens)}')
        problemas += [f'a tabela {t} ficou vazia' for t in TABELAS_CHAVE if not contagens.get(t)]
        if problemas:
            raise RuntimeError('; '.join(problemas))
        ok = True
    except Exception as e:
        log.exception('ensaio de reposição falhou')
        det['erro'] = str(e)[:2000]
    finally:
        if criada:
            try:
                _psql(args, env, f'DROP DATABASE IF EXISTS {BD_ENSAIO} WITH (FORCE)', manutencao)
            except Exception as e:
                log.exception('ensaio: não consegui apagar a base temporária')
                det['aviso'] = f'a base temporária {BD_ENSAIO} não foi apagada: {str(e)[:300]}'
        shutil.rmtree(pasta, ignore_errors=True)
        det['total_s'] = round(time.monotonic() - inicio, 1)
        BackupBD.objects.filter(pk=b.pk).update(ensaio_em=timezone.now(), ensaio_ok=ok, ensaio_detalhe=det)
        cache.delete(TRANCA_ENSAIO)
    b.refresh_from_db()
    if not ok:
        _avisar_ensaio(b)
    return b


def processar_ensaio():
    """Chamado pelo worker: faz o ensaio pedido no admin, ou o periódico quando é devido."""
    pedido = cache.get(PEDIDO_ENSAIO)
    if pedido is not None:
        cache.delete(PEDIDO_ENSAIO)
        b = BackupBD.objects.filter(pk=pedido).first()
        return ensaiar_reposicao(b) if b else None
    if ensaio_devido():
        return ensaiar_reposicao()
    return None


def _avisar_ensaio(b):
    para = destinatarios_alertas()
    if not para:
        return
    try:
        EmailMessage(
            subject='Bende: o ensaio de reposição de um backup falhou',
            body=(f'O backup {b.chave.rsplit("/", 1)[-1]} foi reposto numa base temporária para confirmar que serve '
                  f'e o ensaio falhou.\n\nErro: {b.ensaio_detalhe.get("erro", "")[-1500:]}\n\n'
                  'A base da plataforma não foi tocada. Vê Admin → Backups e o procedimento em docs/REPOR_BACKUP.md.\n\nBende'),
            from_email=settings.DEFAULT_FROM_EMAIL, to=para,
        ).send()
    except Exception:
        log.exception('ensaio: não consegui enviar o aviso de falha')
