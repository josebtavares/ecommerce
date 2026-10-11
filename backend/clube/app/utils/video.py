"""
Otimização de vídeos em segundo plano (banner da loja, vídeo do produto, galeria).

Fluxo:
  1. Um ficheiro de vídeo novo é gravado → signal (app/signals.py) chama `agendar()`,
     que cria uma ConversaoVideo 'pendente' e marca o objeto com <campo>_estado='pendente'.
  2. O worker (`python manage.py processar_videos`) apanha a tarefa, lê o original pelo
     storage do Django (disco local na dev, Cloudflare R2 na prod — o código é o mesmo),
     converte com FFmpeg para MP4 H.264 leve, gera um poster JPG e troca o ficheiro.
  3. Até acabar, a loja continua a mostrar o original. Se o ficheiro for trocado entretanto,
     a tarefa é descartada ('substituido') sem tocar no ficheiro novo.

Configurável por variáveis de ambiente:
  VIDEO_FFMPEG_PRESET   (default 'medium')  — mais lento = ficheiro mais pequeno
  VIDEO_FFMPEG_THREADS  (default 2)         — limita o CPU usado por conversão
"""
import json
import logging
import os
import shutil
import subprocess
import tempfile
import time

from django.apps import apps
from django.core.files import File
from django.db import transaction
from django.utils import timezone

log = logging.getLogger(__name__)

EXTENSOES_VIDEO = ('.mp4', '.webm', '.mov', '.mkv', '.m4v', '.avi')

# Campos com vídeo e como otimizar cada um.
#   lado: maior dimensão (px) · crf: qualidade (menor = melhor) · maxrate: tecto de bitrate
PERFIS = {
    ('loja', 'banner'):      {'lado': 1920, 'crf': 25, 'maxrate': '5M', 'bufsize': '10M'},
    ('produto', 'ficheiro'): {'lado': 1080, 'crf': 24, 'maxrate': '3M', 'bufsize': '6M'},
    ('galeria', 'ficheiro'): {'lado': 1080, 'crf': 24, 'maxrate': '3M', 'bufsize': '6M'},
}
MODELOS = {'loja': 'app.Loja', 'produto': 'app.Produto', 'galeria': 'app.Galeria'}

MAX_FPS        = 30
MAX_TENTATIVAS = 3
PRESET  = os.environ.get('VIDEO_FFMPEG_PRESET', 'medium')
THREADS = os.environ.get('VIDEO_FFMPEG_THREADS', '2')


class TarefaSubstituida(Exception):
    """O ficheiro mudou (ou o objeto foi apagado) antes de a conversão acabar."""


class VideoInvalido(Exception):
    """O ficheiro não se consegue ler como vídeo — repetir não adianta."""


def e_video(nome):
    return bool(nome) and os.path.splitext(str(nome).lower())[1] in EXTENSOES_VIDEO


def _modelo(chave):
    return apps.get_model(MODELOS[chave])


def _conversao():
    return apps.get_model('app', 'ConversaoVideo')


def _apagar_do_storage(storage, nome):
    if not nome:
        return
    try:
        storage.delete(nome)
    except Exception as e:   # um ficheiro órfão não deve estragar a conversão
        log.warning('[video] não consegui apagar %s: %s', nome, e)


# ══════════════════════════════════════════════════════════════
# AGENDAR
# ══════════════════════════════════════════════════════════════

def agendar(instancia, campo):
    """Um ficheiro novo foi gravado em `instancia.<campo>`: agenda a otimização se for vídeo."""
    chave  = instancia._meta.model_name
    if (chave, campo) not in PERFIS:
        return
    ficheiro = getattr(instancia, campo)
    nome     = ficheiro.name if ficheiro else ''

    # tarefas ainda por fazer deste campo já não interessam
    _conversao().objects.filter(
        modelo=chave, objeto_id=instancia.pk, campo=campo, estado='pendente',
    ).update(estado='substituido', terminado_em=timezone.now())

    estado = ''
    if e_video(nome):
        _conversao().objects.create(modelo=chave, objeto_id=instancia.pk, campo=campo, ficheiro=nome)
        estado = 'pendente'

    # o poster antigo era do ficheiro anterior → fila de limpeza (app/utils/limpeza.py)
    poster = getattr(instancia, f'{campo}_poster')
    if poster:
        from .limpeza import agendar_apagar
        agendar_apagar([poster.name], f'poster:{chave}.{campo}')

    # update() em vez de save(): não volta a disparar os signals
    type(instancia).objects.filter(pk=instancia.pk).update(**{
        f'{campo}_estado': estado, f'{campo}_poster': None,
    })
    setattr(instancia, f'{campo}_estado', estado)
    setattr(instancia, f'{campo}_poster', None)


def reprocessar(instancia, campo):
    """Volta a pôr na fila o vídeo actual (ex.: depois de um erro)."""
    ficheiro = getattr(instancia, campo)
    if not ficheiro or not e_video(ficheiro.name):
        return False
    agendar(instancia, campo)
    return True


# ══════════════════════════════════════════════════════════════
# FILA
# ══════════════════════════════════════════════════════════════

def recuperar_interrompidas():
    """Ao arrancar o worker: tarefas que ficaram 'a_processar' (reinício/deploy) voltam à fila."""
    Conversao = _conversao()
    presas = Conversao.objects.filter(estado='a_processar')
    n = 0
    for t in presas:
        t.estado = 'pendente' if t.tentativas < MAX_TENTATIVAS else 'erro'
        if t.estado == 'erro':
            t.erro = (t.erro or '') + '\nInterrompida demasiadas vezes.'
            _marcar_objeto(t, 'erro')
        t.save(update_fields=['estado', 'erro'])
        n += 1
    return n


def proxima_tarefa():
    """Reserva a próxima tarefa pendente (seguro com vários workers)."""
    Conversao = _conversao()
    with transaction.atomic():
        t = (Conversao.objects.select_for_update(skip_locked=True)
             .filter(estado='pendente').order_by('criado_em').first())
        if not t:
            return None
        t.estado      = 'a_processar'
        t.tentativas += 1
        t.iniciado_em = timezone.now()
        t.save(update_fields=['estado', 'tentativas', 'iniciado_em'])
    _marcar_objeto(t, 'a_processar')
    return t


def _ainda_atual(t):
    """O objeto ainda tem o ficheiro desta tarefa? (pode ter sido substituído/apagado)"""
    return _modelo(t.modelo).objects.filter(pk=t.objeto_id, **{t.campo: t.ficheiro}).exists()


def _marcar_objeto(t, estado):
    """Actualiza <campo>_estado no objeto, só se ainda tiver o mesmo ficheiro."""
    _modelo(t.modelo).objects.filter(pk=t.objeto_id, **{t.campo: t.ficheiro}).update(
        **{f'{t.campo}_estado': estado}
    )


# ══════════════════════════════════════════════════════════════
# FFMPEG
# ══════════════════════════════════════════════════════════════

def _correr(cmd, timeout):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f'{cmd[0]} falhou ({r.returncode}): {(r.stderr or "").strip()[-1500:]}')
    return r.stdout


def sondar(caminho):
    """Dados do vídeo via ffprobe: largura, altura, fps, duração, codec."""
    try:
        out = _correr([
            'ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'stream=codec_name,width,height,avg_frame_rate:format=duration',
            '-of', 'json', caminho,
        ], timeout=60)
    except RuntimeError as e:
        raise VideoInvalido(f'Não foi possível ler o vídeo: {e}') from e
    dados   = json.loads(out or '{}')
    streams = dados.get('streams') or []
    if not streams:
        raise VideoInvalido('O ficheiro não tem uma faixa de vídeo válida.')
    s = streams[0]

    fps = 0.0
    try:
        num, den = (s.get('avg_frame_rate') or '0/1').split('/')
        fps = float(num) / float(den) if float(den) else 0.0
    except (ValueError, ZeroDivisionError):
        pass
    try:
        duracao = float((dados.get('format') or {}).get('duration') or 0)
    except ValueError:
        duracao = 0.0

    return {
        'codec': s.get('codec_name') or '', 'largura': s.get('width') or 0,
        'altura': s.get('height') or 0, 'fps': fps, 'duracao': duracao,
    }


def converter(origem, destino, info, perfil):
    """MP4 H.264 leve: limita resolução e fps, qualidade constante, sem áudio, faststart."""
    lado = perfil['lado']
    # a maior dimensão fica ≤ `lado`; a outra acompanha (par, exigido pelo yuv420p).
    # funciona com vídeos verticais e rodados (a rotação é aplicada antes dos filtros).
    filtros = [
        f"scale='if(gte(iw,ih),trunc(min(iw,{lado})/2)*2,-2)':"
        f"'if(gte(iw,ih),-2,trunc(min(ih,{lado})/2)*2)':flags=lanczos"
    ]
    if info['fps'] > MAX_FPS + 0.5:
        filtros.append(f'fps={MAX_FPS}')
    filtros.append('format=yuv420p')

    timeout = max(300, int(info['duracao'] * 20))
    _correr([
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
        '-i', origem,
        '-map', '0:v:0', '-an', '-sn', '-dn',            # só vídeo (os vídeos tocam sempre sem som)
        '-vf', ','.join(filtros),
        '-c:v', 'libx264', '-preset', PRESET, '-crf', str(perfil['crf']),
        '-maxrate', perfil['maxrate'], '-bufsize', perfil['bufsize'],
        '-profile:v', 'high', '-threads', str(THREADS),
        '-movflags', '+faststart',                        # começa a tocar antes de descarregar tudo
        destino,
    ], timeout=timeout)


def extrair_poster(video, destino, info):
    instante = min(1.0, info['duracao'] * 0.25) if info['duracao'] else 0
    _correr([
        'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
        '-ss', f'{instante:.2f}', '-i', video,
        '-frames:v', '1', '-vf', "scale='min(iw,1280)':-2", '-q:v', '4',
        destino,
    ], timeout=60)


# ══════════════════════════════════════════════════════════════
# PROCESSAR UMA TAREFA
# ══════════════════════════════════════════════════════════════

def processar(t):
    """Converte o vídeo de uma tarefa já reservada. Nunca levanta excepções."""
    inicio = time.monotonic()
    pasta  = tempfile.mkdtemp(prefix='video_')
    try:
        _processar(t, pasta)
        t.estado = 'pronto'
        t.erro   = ''
    except TarefaSubstituida:
        t.estado = 'substituido'
    except Exception as e:
        if not _ainda_atual(t):
            # o ficheiro foi trocado (e o anterior apagado) durante a conversão
            t.estado = 'substituido'
        else:
            _falhou(t, e)
    finally:
        shutil.rmtree(pasta, ignore_errors=True)

    t.duracao_s    = round(time.monotonic() - inicio, 1)
    t.terminado_em = timezone.now()
    t.save(update_fields=['estado', 'erro', 'bytes_origem', 'bytes_final', 'duracao_s', 'terminado_em'])
    return t


def _falhou(t, e):
    if isinstance(e, VideoInvalido):
        log.warning('[video] %s: %s', t, e)
        t.erro   = str(e)[-2000:]
        t.estado = 'erro'
        _marcar_objeto(t, 'erro')
        return
    if isinstance(e, (RuntimeError, subprocess.TimeoutExpired)):
        log.warning('[video] erro em %s: %s', t, str(e)[-500:])    # ffmpeg: a mensagem chega
    else:
        log.error('[video] erro em %s', t, exc_info=e)
    t.erro = str(e)[-2000:]
    if t.tentativas < MAX_TENTATIVAS:
        t.estado = 'pendente'          # volta a tentar
        _marcar_objeto(t, 'pendente')
    else:
        t.estado = 'erro'
        _marcar_objeto(t, 'erro')


def _processar(t, pasta):
    Modelo = _modelo(t.modelo)
    obj    = Modelo.objects.filter(pk=t.objeto_id).first()
    if obj is None:
        raise TarefaSubstituida()
    original = getattr(obj, t.campo)
    if not original or original.name != t.ficheiro:
        raise TarefaSubstituida()

    storage = original.storage
    ext     = os.path.splitext(t.ficheiro)[1].lower()
    origem  = os.path.join(pasta, 'origem' + ext)
    destino = os.path.join(pasta, 'video.mp4')
    poster  = os.path.join(pasta, 'poster.jpg')

    # 1. copia o original do storage para o disco (em blocos — não carrega tudo na RAM)
    with storage.open(t.ficheiro, 'rb') as f, open(origem, 'wb') as out:
        shutil.copyfileobj(f, out, 1024 * 1024)
    t.bytes_origem = os.path.getsize(origem)

    # 2. converte e tira o poster
    info = sondar(origem)
    converter(origem, destino, info, PERFIS[(t.modelo, t.campo)])
    extrair_poster(destino, poster, info)

    # se o original já era um MP4 H.264 mais pequeno do que o resultado, fica o original
    usar_convertido = not (
        ext == '.mp4' and info['codec'] == 'h264' and os.path.getsize(destino) >= t.bytes_origem
    )
    t.bytes_final = os.path.getsize(destino) if usar_convertido else t.bytes_origem

    # 3. envia os ficheiros novos para o storage
    base        = os.path.splitext(os.path.basename(t.ficheiro))[0]
    campo_video = getattr(obj, t.campo)
    campo_poster = getattr(obj, f'{t.campo}_poster')
    novo_video  = t.ficheiro
    if usar_convertido:
        with open(destino, 'rb') as f:
            campo_video.save(f'{base}.mp4', File(f), save=False)
        novo_video = campo_video.name
    with open(poster, 'rb') as f:
        campo_poster.save(f'{base}.jpg', File(f), save=False)
    novo_poster = campo_poster.name

    # 4. troca na BD só se o ficheiro ainda for o mesmo (o utilizador pode ter mudado entretanto)
    trocados = Modelo.objects.filter(pk=t.objeto_id, **{t.campo: t.ficheiro}).update(**{
        t.campo: novo_video, f'{t.campo}_poster': novo_poster, f'{t.campo}_estado': 'pronto',
    })
    if not trocados:
        # o ficheiro foi trocado entretanto: o que acabámos de enviar não serve a ninguém.
        # (mesmo que tenha o nome do original — esse já foi apagado ao ser substituído)
        if usar_convertido:
            _apagar_do_storage(storage, novo_video)
        _apagar_do_storage(storage, novo_poster)
        raise TarefaSubstituida()

    if novo_video != t.ficheiro:
        _apagar_do_storage(storage, t.ficheiro)    # o original já não é usado

    log.info('[video] %s: %.1f MB → %.1f MB', t,
             t.bytes_origem / 1e6, (t.bytes_final or 0) / 1e6)
