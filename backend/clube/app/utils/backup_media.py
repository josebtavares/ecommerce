"""
Cópia das fotos e vídeos (storage das lojas) para o armazenamento de backups — incremental.

  copiar(tipo, user)  → uma passagem: copia o que é novo ou mudou; o que a loja apagou passa para
                        media-apagados/AAAAMMDD/ e fica lá BACKUP_MEDIA_APAGADOS_DIAS dias.
  processar()         → chamado pelo worker: a cópia pedida no admin, ou a diária quando é devida.
  repor(...)          → devolve ao storage das lojas os ficheiros que lá faltam (nunca substitui nenhum).

Origens: o bucket público das lojas e o privado (chat, reembolsos, comprovativos); na dev, as pastas
media/ e privado/. Destino: o armazenamento de backups (R2 privado com chave própria; na dev BACKUP_DIR),
nas pastas media/<origem>/ e media-apagados/<dia>/<origem>/. Nunca se copia tudo outra vez: cada passagem
só lê as listas dos dois lados e transfere a diferença.

Proteção: se a origem aparecer vazia, ou se uma passagem fosse tirar da cópia mais de metade dos ficheiros,
pára com erro — é muito mais provável ser uma credencial ou um bucket errado do que as lojas terem apagado tudo.
"""
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.utils import timezone

from ..models import CopiaMedia
from . import backups

log = logging.getLogger(__name__)

TRANCA = 'backup_media:a_correr'
PEDIDO = 'backup_media:pedido'
LIMITE_S = 6 * 3600
PASTA = 'media'
PASTA_APAGADOS = 'media-apagados'
TENTATIVAS_POR_DIA = 3
INTERVALO_TENTATIVAS = timedelta(minutes=30)
MAX_ERROS_GUARDADOS = 20
MINIMO_PROTECAO = 20            # com poucos ficheiros a regra da metade não faz sentido
AVISO_ESPACO_CADA = timedelta(days=7)


class CopiaEmCurso(Exception):
    pass


class OrigemSuspeita(Exception):
    pass


# ── origens (o storage das lojas) ──────────────────────────────────

class _Pasta:
    def __init__(self, raiz):
        self.raiz = Path(raiz)

    def listar(self):
        res = {}
        if self.raiz.exists():
            for p in self.raiz.rglob('*'):
                if p.is_file():
                    st = p.stat()
                    res[p.relative_to(self.raiz).as_posix()] = (st.st_size, st.st_mtime)
        return res

    def abrir(self, chave):
        return open(self.raiz / chave, 'rb'), None

    def existe(self, chave):
        return (self.raiz / chave).exists()

    def guardar_obj(self, fobj, chave, tipo=None):
        destino = self.raiz / chave
        destino.parent.mkdir(parents=True, exist_ok=True)
        with open(destino, 'wb') as f:
            while True:
                bloco = fobj.read(1024 * 1024)
                if not bloco:
                    break
                f.write(bloco)


class _Bucket(backups._R2):
    """Um bucket das lojas, com as credenciais do storage (não as dos backups)."""
    def __init__(self, bucket):
        import boto3
        from botocore.config import Config
        self.bucket = bucket
        self.s3 = boto3.client(
            's3', endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name='auto', config=Config(signature_version='s3v4', retries={'max_attempts': 5}))


def origens():
    """[(nome, origem)] — 'publico' (fotos e vídeos das lojas) e 'privado' (chat, reembolsos, comprovativos)."""
    from ..chat.imagens import _usa_s3
    if _usa_s3():
        res = [('publico', _Bucket(settings.AWS_STORAGE_BUCKET_NAME))]
        if os.environ.get('R2_BUCKET_PRIVADO'):
            res.append(('privado', _Bucket(os.environ['R2_BUCKET_PRIVADO'])))
        return res
    return [('publico', _Pasta(settings.MEDIA_ROOT)), ('privado', _Pasta(Path(settings.BASE_DIR) / 'privado'))]


# ── cópia ──────────────────────────────────────────────────────────

def _encravadas():
    CopiaMedia.objects.filter(estado='a_correr', criado_em__lt=timezone.now() - timedelta(seconds=LIMITE_S)).update(
        estado='erro', erro='Interrompida (o processo parou a meio).')


def _dia(chave):
    """media-apagados/AAAAMMDD/... → date, ou None."""
    partes = chave.split('/')
    try:
        return datetime.strptime(partes[1], '%Y%m%d').date()
    except (IndexError, ValueError):
        return None


def copiar(tipo='automatico', user=None):
    if not cache.add(TRANCA, 1, LIMITE_S):
        raise CopiaEmCurso('Já há uma cópia das fotos e vídeos a correr.')
    _encravadas()
    c = CopiaMedia.objects.create(tipo=tipo, pedido_por=user)
    inicio = time.monotonic()
    erros = []
    try:
        destino = backups.armazenamento()
        hoje = timezone.localdate()
        for nome, origem in origens():
            fonte = {k: v for k, v in origem.listar().items() if not k.endswith('/')}   # «pastas» vazias do R2
            prefixo = f'{PASTA}/{nome}/'
            copia = {k[len(prefixo):]: v for k, v in destino.listar(prefixo).items()}

            sairam = [k for k in copia if k not in fonte]
            if copia and not fonte:
                raise OrigemSuspeita(f'a origem «{nome}» aparece vazia e a cópia tem {len(copia)} ficheiros')
            if len(copia) >= MINIMO_PROTECAO and len(sairam) * 2 > len(copia):
                raise OrigemSuspeita(f'a origem «{nome}» deixou de ter {len(sairam)} dos {len(copia)} ficheiros da cópia')

            for chave, (tamanho, mtime) in fonte.items():
                antes = copia.get(chave)
                if antes and antes[0] == tamanho and antes[1] >= mtime:
                    continue
                try:
                    fobj, tipo_ct = origem.abrir(chave)
                    try:
                        destino.guardar_obj(fobj, prefixo + chave, tipo_ct)
                    finally:
                        fobj.close()
                    c.copiados += 1
                    c.bytes_copiados += tamanho
                except Exception as e:
                    log.warning('cópia media: %s/%s falhou: %s', nome, chave, e)
                    c.falhas += 1
                    if len(erros) < MAX_ERROS_GUARDADOS:
                        erros.append(f'{nome}/{chave}: {str(e)[:200]}')

            for chave in sairam:
                try:
                    destino.mover(prefixo + chave, f'{PASTA_APAGADOS}/{hoje:%Y%m%d}/{nome}/{chave}')
                    c.guardados_apagados += 1
                except Exception as e:
                    c.falhas += 1
                    if len(erros) < MAX_ERROS_GUARDADOS:
                        erros.append(f'{nome}/{chave} (guardar apagado): {str(e)[:200]}')

        limite = hoje - timedelta(days=settings.BACKUP_MEDIA_APAGADOS_DIAS)
        for chave in destino.listar(PASTA_APAGADOS + '/'):
            dia = _dia(chave)
            if dia and dia < limite:
                destino.apagar(chave)
                c.purgados += 1

        tudo = destino.listar('')
        media = [v[0] for k, v in tudo.items() if k.startswith(PASTA + '/')]
        c.ficheiros, c.bytes = len(media), sum(media)
        c.bytes_apagados = sum(v[0] for k, v in tudo.items() if k.startswith(PASTA_APAGADOS + '/'))
        c.bytes_total = sum(v[0] for v in tudo.values())
        if c.falhas:
            c.estado = 'erro'
            c.erro = f'{c.falhas} ficheiro(s) não foram copiados (o worker volta a tentar):\n' + '\n'.join(erros)
        else:
            c.estado = 'ok'
    except Exception as e:
        log.exception('cópia das fotos e vídeos falhou')
        c.estado, c.erro = 'erro', str(e)[:4000]
    finally:
        c.duracao_s = round(time.monotonic() - inicio, 1)
        c.save()
        cache.delete(TRANCA)
    if c.estado == 'erro':
        _avisar(c)
    _avisar_espaco(c)
    return c


# ── quando ─────────────────────────────────────────────────────────

def devida(agora=None):
    """Uma vez por dia, depois da hora do backup da base; até 3 tentativas com 30 minutos de intervalo.
    Uma cópia manual bem feita depois dessa hora conta como a do dia (a seguinte não teria nada para copiar)."""
    agora = timezone.localtime(agora or timezone.now())
    if agora.hour < settings.BACKUP_HORA:
        return False
    hoje = CopiaMedia.objects.filter(criado_em__gte=agora.replace(hour=settings.BACKUP_HORA, minute=0, second=0, microsecond=0))
    if hoje.filter(estado__in=('ok', 'a_correr')).exists():
        return False
    falhas = hoje.filter(tipo='automatico', estado='erro')
    if falhas.count() >= TENTATIVAS_POR_DIA:
        return False
    ultima = falhas.order_by('-criado_em').first()
    return not ultima or agora - ultima.criado_em >= INTERVALO_TENTATIVAS


def pedir(user_id):
    if cache.get(TRANCA) or cache.get(PEDIDO):
        raise CopiaEmCurso('Já há uma cópia das fotos e vídeos pedida ou a correr.')
    cache.set(PEDIDO, user_id or 0, 3600)


def em_curso():
    return bool(cache.get(TRANCA) or cache.get(PEDIDO))


def processar(verificar_devida=True):
    pedido = cache.get(PEDIDO)
    if pedido is not None:
        cache.delete(PEDIDO)
        from django.contrib.auth.models import User
        return copiar('manual', User.objects.filter(pk=pedido).first())
    if verificar_devida and devida():
        return copiar('automatico')
    return None


# ── repor ──────────────────────────────────────────────────────────

def repor(origem='publico', dia=None, prefixo='', simular=True):
    """Copia da cópia de segurança para o storage das lojas os ficheiros que lá FALTAM (nunca substitui).
    dia=AAAAMMDD repõe a partir de media-apagados/ desse dia. Devolve {'repostos', 'bytes', 'ja_existiam', 'falhas'}."""
    alvo = dict(origens()).get(origem)
    if alvo is None:
        raise ValueError(f'origem desconhecida: {origem}')
    base = f'{PASTA_APAGADOS}/{dia}/{origem}/' if dia else f'{PASTA}/{origem}/'
    destino = backups.armazenamento()
    existentes = alvo.listar()
    res = {'repostos': 0, 'bytes': 0, 'ja_existiam': 0, 'falhas': []}
    for chave, (tamanho, _) in sorted(destino.listar(base + prefixo).items()):
        nome = chave[len(base):]
        if nome in existentes:
            res['ja_existiam'] += 1
            continue
        if not simular:
            try:
                fobj, tipo = destino.abrir(chave)
                try:
                    alvo.guardar_obj(fobj, nome, tipo)
                finally:
                    fobj.close()
            except Exception as e:
                res['falhas'].append(f'{nome}: {str(e)[:200]}')
                continue
        res['repostos'] += 1
        res['bytes'] += tamanho
    return res


# ── avisos ─────────────────────────────────────────────────────────

def _enviar(assunto, corpo):
    para = backups.destinatarios_alertas()
    if not para:
        return False
    try:
        EmailMessage(subject=assunto, body=corpo, from_email=settings.DEFAULT_FROM_EMAIL, to=para).send()
        return True
    except Exception:
        log.exception('cópia media: não consegui enviar o aviso')
        return False


def _avisar(c):
    _enviar('Bende: a cópia das fotos e vídeos falhou',
            f'A cópia {c.get_tipo_display().lower()} das fotos e vídeos de '
            f'{timezone.localtime(c.criado_em):%d/%m/%Y %H:%M} falhou.\n\n{c.erro[-1500:]}\n\n'
            'O worker volta a tentar daqui a 30 minutos (até 3 vezes por dia). Os ficheiros que já estavam '
            'copiados continuam guardados. Vê Admin → Backups.\n\nBende')


def _avisar_espaco(c):
    limite = settings.BACKUP_LIMITE_GB * 1e9
    if not c.bytes_total or c.bytes_total < limite:
        return
    if CopiaMedia.objects.filter(aviso_espaco=True, criado_em__gte=timezone.now() - AVISO_ESPACO_CADA).exists():
        return
    if _enviar('Bende: os backups estão perto do limite grátis do R2',
               f'O armazenamento de backups tem {c.bytes_total / 1e9:.1f} GB (o aviso está nos '
               f'{settings.BACKUP_LIMITE_GB:g} GB; o Cloudflare R2 dá 10 GB por mês grátis e depois cobra cerca de '
               '0,015 USD por GB por mês).\n\n'
               f'Base de dados e exportações: {(c.bytes_total - c.bytes - c.bytes_apagados) / 1e9:.2f} GB\n'
               f'Fotos e vídeos: {c.bytes / 1e9:.2f} GB\n'
               f'Fotos e vídeos apagados pelas lojas (guardados {settings.BACKUP_MEDIA_APAGADOS_DIAS} dias): '
               f'{c.bytes_apagados / 1e9:.2f} GB\n\n'
               'Nada deixa de funcionar: só passa a haver custo. Vê Admin → Backups.\n\nBende'):
        CopiaMedia.objects.filter(pk=c.pk).update(aviso_espaco=True)
        c.aviso_espaco = True
