"""
Arquivo fiscal grande demais para descarregar na hora (Views/faturacaoView.arquivo_zip e admin_bende_arquivo):
o pedido vai para a fila, o worker (manage.py processar_videos) prepara o ZIP, guarda-o no armazenamento privado
dos backups (tem dados dos clientes) e avisa quem pediu (notificação + email). A página da Faturação lista os
arquivos preparados; descarrega-se por link de 5 minutos. Apagam-se ao fim de DIAS_VALIDADE dias.

  pedir(alvo, obj, de, ate, com_bende, origem, user, nome) → ArquivoFiscal (o mesmo, se já está um igual na fila)
  pedir_resposta(...)                                      → 202 com o pedido (409/429 se não dá)
  processar_fila() / expirar() / gerar(a)                  → worker
"""
import logging
import shutil
import tempfile
import zipfile
from datetime import timedelta
from pathlib import Path

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from ..models import ArquivoFiscal
from . import backups

log = logging.getLogger(__name__)

DIAS_VALIDADE = 7
MAX_POR_DIA = 10          # por loja / POS / Bende
ENCRAVADO = timedelta(hours=2)


class ArquivoEmCurso(Exception):
    pass


class LimiteArquivos(Exception):
    pass


def filtro(alvo, obj=None):
    if alvo == 'loja':
        return {'alvo': 'loja', 'loja': obj}
    if alvo == 'pos':
        return {'alvo': 'pos', 'pos': obj}
    return {'alvo': 'bende'}


def _nome_alvo(a):
    return 'Bende' if a.alvo == 'bende' else (a.loja.nome if a.alvo == 'loja' else f'POS {a.pos.nome}')


def periodo(a):
    if a.alvo == 'bende':
        return f'{a.de:%m/%Y} a {a.ate:%m/%Y}' if a.de and a.ate else ''
    if a.de and a.ate:
        return f'{a.de:%d/%m/%Y} a {a.ate:%d/%m/%Y}'
    if a.de:
        return f'desde {a.de:%d/%m/%Y}'
    return f'até {a.ate:%d/%m/%Y}' if a.ate else 'desde sempre'


# ── pedir ──────────────────────────────────────────────────────────

def pedir(alvo, obj, de, ate, com_bende=True, origem='admin', user=None, nome=''):
    f = filtro(alvo, obj)
    with transaction.atomic():
        ativos = ArquivoFiscal.objects.select_for_update().filter(**f, estado__in=('pendente', 'a_correr'))
        igual = ativos.filter(de=de, ate=ate, com_bende=com_bende).first()
        if igual:
            return igual
        if ativos.exists():
            raise ArquivoEmCurso('Já há um arquivo a ser preparado — espera que fique pronto (avisamos-te).')
        if ArquivoFiscal.objects.filter(**f, criado_em__gte=timezone.now() - timedelta(days=1)).count() >= MAX_POR_DIA:
            raise LimiteArquivos(f'Já foram pedidos {MAX_POR_DIA} arquivos nas últimas 24 horas. Tenta amanhã.')
        return ArquivoFiscal.objects.create(**f, de=de, ate=ate, com_bende=com_bende, origem=origem,
                                            pedido_por=user if user and user.is_authenticated else None,
                                            pedido_por_nome=(nome or (user.get_full_name() or user.username if user else ''))[:150])


def pedir_resposta(alvo, obj, de, ate, com_bende, origem, user, nome, motivo):
    try:
        a = pedir(alvo, obj, de, ate, com_bende, origem, user, nome)
    except ArquivoEmCurso as x:
        return Response({'detail': str(x)}, status=status.HTTP_409_CONFLICT)
    except LimiteArquivos as x:
        return Response({'detail': str(x)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
    aviso = 'Avisamos-te (notificação e email) quando estiver pronto.' if a.pedido_por_id else 'Aparece na lista quando estiver pronto.'
    return Response({'em_fila': True, 'arquivo': item(a),
                     'detail': f'{motivo}: o arquivo vai ser preparado em segundo plano. {aviso}'},
                    status=status.HTTP_202_ACCEPTED)


def item(a, admin=False):
    return {
        'id': a.id, 'alvo': a.alvo, 'estado': a.estado, 'estado_label': a.get_estado_display(),
        'de': a.de, 'ate': a.ate, 'periodo': periodo(a), 'com_bende': a.com_bende,
        'pedido_por': ('Equipa Bende' if a.origem == 'admin' and not admin else a.pedido_por_nome),
        'criado_em': a.criado_em, 'concluido_em': a.concluido_em, 'expira_em': a.expira_em,
        'tamanho': a.tamanho, 'descargas': a.descargas,
        'avisos': len([x for x in a.avisos.splitlines() if x.strip()]),
        'erro': a.erro[-300:] if a.estado == 'erro' else '', 'disponivel': a.estado == 'ok',
    }


def lista(request, qs, admin=False):
    from ..Views.faturacaoView import _paginar
    pagina, total = _paginar(request, qs, 10)
    return Response({'count': total, 'results': [item(a, admin) for a in pagina],
                     'em_curso': qs.filter(estado__in=('pendente', 'a_correr')).exists(),
                     'dias_validade': DIAS_VALIDADE})


# ── worker ─────────────────────────────────────────────────────────

def processar_fila():
    ArquivoFiscal.objects.filter(estado='a_correr', iniciado_em__lt=timezone.now() - ENCRAVADO).update(
        estado='erro', erro='Interrompido (o processo parou a meio).')
    with transaction.atomic():
        a = (ArquivoFiscal.objects.select_for_update(skip_locked=True)
             .filter(estado='pendente').order_by('criado_em').first())
        if not a:
            return False
        a.estado, a.iniciado_em = 'a_correr', timezone.now()
        a.save(update_fields=['estado', 'iniciado_em'])
    gerar(a)
    return True


def expirar(agora=None):
    agora = agora or timezone.now()
    n = 0
    arm = backups.armazenamento()
    for a in ArquivoFiscal.objects.filter(estado='ok', expira_em__lt=agora):
        try:
            if a.chave:
                arm.apagar(a.chave)
            a.estado = 'expirada'
            a.save(update_fields=['estado'])
            n += 1
        except Exception:
            log.exception('arquivo fiscal: não consegui apagar %s', a.chave)
    return n


def nome_ficheiro(a):
    from ..Views import faturacaoView as fat
    if a.alvo == 'bende':
        return fat.nome_arquivo_bende(a.de, a.ate + timedelta(days=1))
    obj = a.loja if a.alvo == 'loja' else a.pos
    return f'arquivo-fiscal-{a.alvo}-{obj.id}-{a.de or "inicio"}-{a.ate or timezone.localdate(a.criado_em)}.zip'


def gerar(a):
    from ..Views import faturacaoView as fat
    pasta = tempfile.mkdtemp(prefix='arquivo-fiscal-')
    try:
        nome = nome_ficheiro(a)
        ficheiro = Path(pasta) / nome
        with zipfile.ZipFile(ficheiro, 'w', zipfile.ZIP_DEFLATED) as zf:
            if a.alvo == 'bende':
                faltas = fat.escrever_arquivo_bende(zf, a.de, a.ate + timedelta(days=1))
            else:
                faltas = fat.escrever_arquivo(zf, a.loja if a.alvo == 'loja' else a.pos, a.alvo, a.de, a.ate, a.com_bende)
        dono = 'bende' if a.alvo == 'bende' else f'{a.alvo}-{a.loja_id or a.pos_id}'
        chave = f'arquivos-fiscais/{dono}/{a.id}-{nome}'
        backups.armazenamento().guardar(ficheiro, chave)
        a.chave, a.tamanho, a.estado = chave, ficheiro.stat().st_size, 'ok'
        a.avisos = '\n'.join(faltas)[:20000]
        a.expira_em = timezone.now() + timedelta(days=DIAS_VALIDADE)
    except Exception as e:
        log.exception('%s falhou', a)
        a.estado, a.erro = 'erro', str(e)[:4000]
    finally:
        shutil.rmtree(pasta, ignore_errors=True)
        a.concluido_em = timezone.now()
        a.save(update_fields=['chave', 'tamanho', 'estado', 'avisos', 'expira_em', 'erro', 'concluido_em'])
    _avisar(a)
    return a


def link(a):
    if a.origem == 'admin':
        return '/admin/faturacao?tab=bende' if a.alvo == 'bende' else f'/admin/faturacao?ficha={a.alvo}-{a.loja_id or a.pos_id}'
    if a.origem == 'loja':
        return f'/loja/{a.loja_id}/backoffice/faturacao'
    return '/pos/dashboard/faturacao'


def _avisar(a):
    """Notificação + email a quem pediu (os membros do POS não têm conta Bende: veem na lista)."""
    u = a.pedido_por
    if not u:
        return
    ok = a.estado == 'ok'
    titulo = f'Arquivo fiscal de «{_nome_alvo(a)}» ' + ('pronto' if ok else 'falhou')
    texto = (f'O arquivo fiscal ({periodo(a)}) está pronto. Descarrega-o na Faturação — fica disponível {DIAS_VALIDADE} dias.'
             if ok else 'Não foi possível preparar o arquivo fiscal. Tenta outra vez; se voltar a falhar, fala com o suporte.')
    utilizador = getattr(u, 'utilizador', None)
    if utilizador:
        try:
            from ..Views.notificacaoView import notificar
            notificar(utilizador, 'exportacao_pronta', titulo, texto, loja=a.loja, link=link(a))
        except Exception:
            log.exception('arquivo fiscal: não consegui notificar')
    try:
        from .emails_fiscais import _enviar, _link
        _enviar(u.email, titulo, texto, botao=('Abrir a Faturação', _link(link(a))) if ok else None)
    except Exception:
        log.exception('arquivo fiscal: não consegui enviar o email')
