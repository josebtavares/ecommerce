"""
Documentos legais da loja (models.DocumentoLoja): o dono envia, se quiser, o documento de identificação,
o início de atividade / certidão comercial, o NIF, licenças… e a Bende verifica-os no Admin → Lojas.

• Opcionais: quem vende coisas pessoais em casa não precisa. O admin pode torná-los obrigatórios para uma
  loja (Loja.documentos_obrigatorios) — então "Loja verificada" entra nos requisitos para publicar (prontidao.py).
• Loja verificada = identificação do titular + início de atividade/certidão aprovados e dentro da validade.
  O selo só aparece ao público com ConfiguracaoPlataforma.mostrar_selo_verificada (desligado por defeito).
• Ficheiros privados (bucket R2 privado / pasta privado/ na dev): PDF tal como vem (só se começa por %PDF-);
  JPG/PNG reconvertidos para JPEG sem metadados (o GPS das fotos), até 3000 px. Máx. 10 MB.
• Abrem-se por link assinado de 2 minutos, pedido por quem pode (o dono ou admin com verificar_documentos);
  cada abertura, envio, decisão e remoção fica em AcessoDocumentoLoja (o dono vê as consultas da Bende).
• Apagar o documento (ou a loja, ou a conta do dono) apaga o ficheiro.
"""
import logging
import os
import uuid
from datetime import timedelta
from io import BytesIO

from django.core import signing
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone

log = logging.getLogger(__name__)

TAMANHO_MAX = 10 * 1024 * 1024
PIXEIS_MAX = 60_000_000
LADO_MAX = 3000
MAX_POR_LOJA = 30
VALIDADE_LINK = 120                  # segundos
SALT = 'documento-loja'
PRINCIPAIS = ('identificacao', 'atividade')
AVISO_DIAS = 30                      # avisa o dono quando falta isto para expirar


class ErroDocumento(Exception):
    pass


def disponivel():
    from ..chat.imagens import imagens_disponiveis
    return imagens_disponiveis()


# ── ficheiros ────────────────────────────────────────────────────────

def preparar(ficheiro):
    """→ (ContentFile, formato). Valida pelo conteúdo, nunca pela extensão."""
    if not ficheiro:
        raise ErroDocumento('Escolhe o ficheiro.')
    if ficheiro.size > TAMANHO_MAX:
        raise ErroDocumento('O ficheiro tem mais de 10 MB.')
    ficheiro.seek(0)
    inicio = ficheiro.read(8)
    ficheiro.seek(0)
    if inicio.startswith(b'%PDF-'):
        return ContentFile(ficheiro.read(), name=f'{uuid.uuid4().hex}.pdf'), 'pdf'
    from PIL import Image, ImageOps, UnidentifiedImageError
    Image.MAX_IMAGE_PIXELS = PIXEIS_MAX
    try:
        img = Image.open(ficheiro)
        if img.format not in ('JPEG', 'PNG'):
            raise ErroDocumento('Só PDF, JPG ou PNG.')
        img.load()
        img = ImageOps.exif_transpose(img)
    except ErroDocumento:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError):
        raise ErroDocumento('Só PDF, JPG ou PNG (o ficheiro não abre).')
    if img.mode not in ('RGB', 'L'):
        fundo = Image.new('RGB', img.size, 'white')
        if 'A' in img.getbands():
            fundo.paste(img.convert('RGBA'), mask=img.convert('RGBA').split()[-1])
        else:
            fundo.paste(img.convert('RGB'))
        img = fundo
    img.thumbnail((LADO_MAX, LADO_MAX))
    saida = BytesIO()
    img.save(saida, 'JPEG', quality=88, optimize=True)      # sem exif= → sai sem metadados
    return ContentFile(saida.getvalue(), name=f'{uuid.uuid4().hex}.jpg'), 'jpg'


def nome_limpo(nome):
    base = os.path.basename(str(nome or '')).replace('\x00', '')
    return ''.join(c for c in base if c.isprintable())[:120]


def _apagar_ficheiro(nome, armazenamento):
    try:
        armazenamento.delete(nome)
    except Exception:
        log.warning('documentos: não apagou %s', nome)


@receiver(post_delete, sender='app.DocumentoLoja')
def _ao_apagar(sender, instance, **kwargs):
    if instance.ficheiro:
        nome, arm = instance.ficheiro.name, instance.ficheiro.storage
        transaction.on_commit(lambda: _apagar_ficheiro(nome, arm))


# ── estado ───────────────────────────────────────────────────────────

def hoje():
    from .horarios import fuso
    return timezone.now().astimezone(fuso()).date()


def _valido_q(prefixo=''):
    return Q(**{f'{prefixo}estado': 'aprovado'}) & (Q(**{f'{prefixo}validade__isnull': True})
                                                    | Q(**{f'{prefixo}validade__gte': hoje()}))


def expirado(d):
    return bool(d.validade and d.validade < hoje())


def anotar_verificada(qs):
    """Lojas com `verificada` (identificação + atividade aprovados e válidos)."""
    from ..models import DocumentoLoja
    return qs.annotate(**{f'_doc_{t}': Exists(DocumentoLoja.objects.filter(_valido_q(), loja=OuterRef('pk'), tipo=t))
                          for t in PRINCIPAIS})


def verificada(loja):
    if all(hasattr(loja, f'_doc_{t}') for t in PRINCIPAIS):
        return all(getattr(loja, f'_doc_{t}') for t in PRINCIPAIS)
    validos = set(loja.documentos.filter(_valido_q(), tipo__in=PRINCIPAIS).values_list('tipo', flat=True))
    return validos >= set(PRINCIPAIS)


def resumo(loja):
    """{verificada, em_falta: [títulos], pendentes, obrigatorios}"""
    from ..models import DocumentoLoja
    docs = list(loja.documentos.all())
    validos = {d.tipo for d in docs if d.estado == 'aprovado' and not expirado(d)}
    nomes = dict(DocumentoLoja.TIPOS)
    return {
        'verificada': set(PRINCIPAIS) <= validos,
        'em_falta': [nomes[t] for t in PRINCIPAIS if t not in validos],
        'pendentes': sum(d.estado == 'pendente' for d in docs),
        'obrigatorios': loja.documentos_obrigatorios,
    }


def selo_publico(loja):
    """True/False só quando o selo está ligado para o público; senão None (o campo não diz nada)."""
    from ..models import ConfiguracaoPlataforma
    if not ConfiguracaoPlataforma.atual().mostrar_selo_verificada:
        return None
    return verificada(loja)


# ── payloads e links ─────────────────────────────────────────────────

def _data(d):
    from .horarios import fuso
    return d.astimezone(fuso()).strftime('%d/%m/%Y %H:%M') if d else None


def payload(d, admin=False):
    out = {
        'id': d.id, 'tipo': d.tipo, 'tipo_nome': d.get_tipo_display(), 'descricao': d.descricao,
        'formato': d.formato, 'tamanho': d.tamanho, 'nome_original': d.nome_original,
        'estado': d.estado, 'estado_nome': d.get_estado_display(), 'motivo': d.motivo,
        'validade': d.validade.isoformat() if d.validade else None, 'expirado': expirado(d),
        'enviado_em': _data(d.enviado_em), 'revisto_em': _data(d.revisto_em),
    }
    if admin:
        out['enviado_por'] = d.enviado_por.username if d.enviado_por else ''
        out['revisto_por'] = d.revisto_por.username if d.revisto_por else ''
    return out


def acessos(loja, so_bende=False, n=20):
    from ..models import AcessoDocumentoLoja
    qs = AcessoDocumentoLoja.objects.filter(loja=loja)
    if so_bende:
        qs = qs.filter(pela_bende=True)
    return [{'id': a.id, 'acao': a.acao, 'acao_nome': a.get_acao_display(), 'tipo': a.tipo,
             'quem': a.nome if not so_bende else 'Bende', 'detalhe': a.detalhe, 'quando': _data(a.criado_em)}
            for a in qs.select_related(None)[:n]]


def registar(request, loja, acao, documento=None, pela_bende=False, detalhe='', tipo=''):
    from ..models import AcessoDocumentoLoja
    AcessoDocumentoLoja.objects.create(
        documento=documento, loja=loja, loja_nome=loja.nome if loja else '',
        tipo=tipo or (documento.tipo if documento else ''), acao=acao,
        utilizador=request.user if request and request.user.is_authenticated else None,
        nome=request.user.username if request and request.user.is_authenticated else '',
        pela_bende=pela_bende, detalhe=detalhe[:300],
        ip=(request.META.get('REMOTE_ADDR') or None) if request else None)


def assinar(documento_id, utilizador_id):
    return signing.dumps({'d': documento_id, 'u': utilizador_id}, salt=SALT, compress=True)


def ler_assinatura(token):
    try:
        d = signing.loads(token, salt=SALT, max_age=VALIDADE_LINK)
        return int(d['d']), int(d['u'])
    except (signing.BadSignature, KeyError, TypeError, ValueError):
        return None


def pode_abrir(utilizador, documento):
    """O dono da loja, ou um admin com verificar_documentos (verificado outra vez ao servir o ficheiro)."""
    if not utilizador or not utilizador.is_active:
        return False
    if utilizador.user.is_staff and utilizador.pode_admin('verificar_documentos'):
        return True
    from ..models import UtilizadorLoja
    membro = UtilizadorLoja.obter_membro(documento.loja, utilizador)
    return bool(membro and membro.pode('gerir_documentos'))


# ── acções ───────────────────────────────────────────────────────────

def enviar(request, loja, tipo, ficheiro, descricao='', validade=None):
    from ..models import DocumentoLoja
    if tipo not in dict(DocumentoLoja.TIPOS):
        raise ErroDocumento('Escolhe o tipo de documento.')
    if not disponivel():
        raise ErroDocumento('O envio de documentos não está disponível de momento.')
    if loja.documentos.count() >= MAX_POR_LOJA:
        raise ErroDocumento(f'Máximo de {MAX_POR_LOJA} documentos — apaga os que já não precisas.')
    descricao = ' '.join(str(descricao or '').split())[:120]
    if tipo == 'outro' and len(descricao) < 3:
        raise ErroDocumento('Diz que documento é (ex.: "Certificado de formação em higiene alimentar").')
    if validade and validade < hoje():
        raise ErroDocumento('Este documento já expirou — envia um dentro da validade.')
    conteudo, formato = preparar(ficheiro)
    with transaction.atomic():
        d = DocumentoLoja(loja=loja, tipo=tipo, descricao=descricao, formato=formato, tamanho=conteudo.size,
                          nome_original=nome_limpo(ficheiro.name), validade=validade, enviado_por=request.user)
        d.ficheiro.save(conteudo.name, conteudo, save=True)
        registar(request, loja, 'enviar', d)
        transaction.on_commit(lambda: _avisar_admins(loja, d))
    return d


def _avisar_admins(loja, d):
    from ..models import Notificacao, Utilizador
    admins = [u for u in Utilizador.objects.filter(user__is_staff=True, user__is_active=True).select_related('user')
              if u.pode_admin('verificar_documentos')]
    Notificacao.objects.bulk_create([Notificacao(
        utilizador=u, tipo='documento_loja', titulo='Documento para verificar',
        mensagem=f'A loja "{loja.nome}" enviou: {d.get_tipo_display()}.', loja=loja,
        link=f'/admin/lojas/{loja.id}') for u in admins])


def decidir(request, d, acao, motivo='', validade=None):
    """Admin aprova (com validade opcional) ou rejeita (com motivo). Aprovar substitui os do mesmo tipo."""
    from ..models import DocumentoLoja
    from ..Views.notificacaoView import notificar
    motivo = ' '.join(str(motivo or '').split())[:300]
    if acao == 'rejeitar' and len(motivo) < 5:
        raise ErroDocumento('Diz à loja porque foi rejeitado (ex.: "ilegível", "nome diferente do titular").')
    if acao not in ('aprovar', 'rejeitar'):
        raise ErroDocumento('Acção inválida.')
    with transaction.atomic():
        d = DocumentoLoja.objects.select_for_update().select_related('loja__dono__user').get(pk=d.pk)
        if acao == 'aprovar' and validade and validade < hoje():
            raise ErroDocumento('Essa validade já passou — rejeita o documento e pede um válido.')
        antes = verificada(d.loja)
        d.estado = 'aprovado' if acao == 'aprovar' else 'rejeitado'
        d.motivo = '' if acao == 'aprovar' else motivo
        if acao == 'aprovar':
            d.validade = validade if validade is not None else d.validade
        d.aviso = ''
        d.revisto_por, d.revisto_em = request.user, timezone.now()
        d.save()
        substituidos = 0
        if acao == 'aprovar' and d.tipo != 'outro':
            # o novo aprovado substitui os anteriores do mesmo tipo (os ficheiros vão com eles)
            velhos = d.loja.documentos.filter(tipo=d.tipo).exclude(pk=d.pk)
            substituidos = velhos.count()
            for v in velhos:
                v.delete()
        registar(request, d.loja, acao, d, pela_bende=True,
                 detalhe=motivo if acao == 'rejeitar' else (f'validade {d.validade:%d/%m/%Y}' if d.validade else ''))
        loja = d.loja
        agora = verificada(loja)
        if acao == 'aprovar':
            titulo = 'Loja verificada' if agora and not antes else 'Documento aprovado'
            texto = f'{d.get_tipo_display()} aprovado.' + (' A tua loja está verificada.' if agora and not antes else '')
        else:
            titulo = 'Documento rejeitado'
            texto = f'{d.get_tipo_display()}: {motivo} Envia outro em Configurações → Documentos.'
        transaction.on_commit(lambda: notificar(loja.dono, 'documento_loja', titulo, texto, loja=loja,
                                                link=f'/loja/{loja.id}/backoffice/configuracoes'))
    return d, substituidos


def apagar(request, d):
    with transaction.atomic():
        registar(request, d.loja, 'apagar', d, detalhe=d.get_tipo_display())
        d.delete()


def mudar_obrigatorios(request, loja, valor):
    from ..Views.notificacaoView import notificar
    if loja.documentos_obrigatorios == valor:
        return
    loja.documentos_obrigatorios = valor
    loja.save(update_fields=['documentos_obrigatorios'])
    registar(request, loja, 'obrigatorios', pela_bende=True, detalhe='obrigatórios' if valor else 'opcionais')
    if valor and not verificada(loja):
        notificar(loja.dono, 'documento_loja', 'Documentos pedidos pela Bende',
                  'Para publicar a loja, envia o documento de identificação e o início de atividade (ou certidão '
                  'comercial) em Configurações → Documentos.', loja=loja, link=f'/loja/{loja.id}/backoffice/configuracoes')


def apagar_da_conta(utilizador):
    """Conta eliminada: os documentos das lojas do dono vão-se (os ficheiros com eles)."""
    from ..models import DocumentoLoja
    for d in DocumentoLoja.objects.filter(loja__dono=utilizador):
        d.delete()


# ── worker: validades ────────────────────────────────────────────────

def avisar_validades():
    """Uma vez por dia chega: avisa o dono 30 dias antes e no dia em que um documento aprovado expira."""
    from ..models import DocumentoLoja
    from ..Views.notificacaoView import notificar
    h = hoje()
    n = 0
    a_expirar = DocumentoLoja.objects.filter(estado='aprovado', aviso='', validade__isnull=False,
                                             validade__gte=h, validade__lte=h + timedelta(days=AVISO_DIAS))
    expirados = DocumentoLoja.objects.filter(estado='aprovado', validade__lt=h).exclude(aviso='expirado')
    for qs, aviso in ((a_expirar, 'a_expirar'), (expirados, 'expirado')):
        for d in qs.select_related('loja__dono__user')[:200]:
            loja = d.loja
            if aviso == 'a_expirar':
                titulo, texto = 'Documento a expirar', (f'{d.get_tipo_display()} expira a {d.validade:%d/%m/%Y}. '
                                                        'Envia o novo em Configurações → Documentos.')
            else:
                titulo, texto = 'Documento expirado', (f'{d.get_tipo_display()} expirou a {d.validade:%d/%m/%Y}'
                                                       + (' — a loja deixou de estar verificada.' if d.tipo in PRINCIPAIS else '.')
                                                       + ' Envia o novo em Configurações → Documentos.')
            DocumentoLoja.objects.filter(pk=d.pk).update(aviso=aviso)
            try:
                notificar(loja.dono, 'documento_loja', titulo, texto, loja=loja,
                          link=f'/loja/{loja.id}/backoffice/configuracoes')
            except Exception:
                log.exception('documentos: aviso de validade falhou (%s)', d.pk)
            n += 1
    return n
