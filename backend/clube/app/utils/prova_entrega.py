"""
Prova de entrega — foto, assinatura do cliente e nome de quem recebeu. TUDO OPCIONAL.

- Grava-se depois de a entrega estar marcada como feita (status 'entregue'): marcar entregue nunca depende disto
  (o cliente pode não estar para assinar, a câmara pode falhar). Pode juntar-se até PRAZO_H horas depois.
- Cada parte grava-se uma vez só (é prova: não se troca nem apaga).
- Quem junta e quem vê: o condutor da entrega e quem gere entregas na loja. Ficheiros privados, servidos por link
  assinado (1 h) que volta a verificar o acesso — como as fotos dos reembolsos.
"""
from datetime import timedelta

from django.core import signing
from django.utils import timezone

PRAZO_H = 24
SALT = 'prova-entrega'
VALIDADE = 3600
NOME_MAX = 100
PARTES = ('foto', 'assinatura')
LINKS = PARTES + ('talao',)      # talao: foto do talão do envio por transportadora (utils/envios.py)


class ErroProva(Exception):
    pass


def pode_ver(utilizador, entrega):
    from ..models import UtilizadorLoja
    m = UtilizadorLoja.obter_membro(entrega.encomenda.loja, utilizador)
    if not m or not m.pode('gerir_entregas'):
        return False
    if m.role == 'condutor':
        return bool(entrega.condutor_id and entrega.condutor.utilizador_id == utilizador.id)
    return True


def assinar(entrega_id, parte, utilizador_id, admin=False):
    # admin: o admin a ver o backoffice em modo de leitura (utils/ver_loja.py) — o <img> não leva esse token
    return signing.dumps({'e': entrega_id, 'p': parte, 'u': utilizador_id, 'a': bool(admin)}, salt=SALT, compress=True)


def ler(token):
    try:
        d = signing.loads(token, salt=SALT, max_age=VALIDADE)
        if d['p'] not in LINKS:
            return None
        return int(d['e']), d['p'], int(d['u']), bool(d.get('a'))
    except (signing.BadSignature, KeyError, TypeError, ValueError):
        return None


def dados(entrega, request):
    """Para o EntregaSerializer: None se não há prova; links só para quem pode ver."""
    tem = {p: bool(getattr(entrega, f'prova_{p}')) for p in PARTES}
    if not (tem['foto'] or tem['assinatura'] or entrega.recebido_por_nome):
        return None
    from .ver_loja import a_ver
    u = getattr(getattr(request, 'user', None), 'utilizador', None)
    admin = bool(u and a_ver(entrega.encomenda.loja_id, u))
    res = {'recebido_por': entrega.recebido_por_nome, 'em': entrega.prova_em}
    for p in PARTES:
        res[p] = (request.build_absolute_uri(f'/app/entregas/{entrega.id}/prova/{p}/?t={assinar(entrega.id, p, u.id, admin)}')
                  if tem[p] and u else None)
    return res


def pode_juntar(entrega, agora=None):
    """None se ainda se pode juntar prova; senão a razão."""
    if entrega.status != 'entregue':
        return 'Só depois de marcar a entrega como feita.'
    agora = agora or timezone.now()
    if entrega.data_entrega and agora - entrega.data_entrega > timedelta(hours=PRAZO_H):
        return f'Já passaram mais de {PRAZO_H} h desde a entrega.'
    return None


def preparar(ficheiro):
    """Valida e converte (WebP, sem EXIF) fora da transacção → ContentFile."""
    from ..chat import imagens
    if not ficheiro:
        return None
    if not imagens.imagens_disponiveis():
        raise ErroProva('O envio de imagens não está disponível de momento.')
    try:
        conteudo, _, _ = imagens.processar(ficheiro)
    except imagens.ImagemInvalida as e:
        raise ErroProva(str(e))
    return conteudo


def gravar(entrega, foto=None, assinatura=None, nome=''):
    """entrega já bloqueada (select_for_update). foto/assinatura: ContentFile de preparar()."""
    erro = pode_juntar(entrega)
    if erro:
        raise ErroProva(erro)
    nome = (nome or '').strip()[:NOME_MAX]
    if not (foto or assinatura or nome):
        raise ErroProva('Junta uma foto, a assinatura ou o nome de quem recebeu.')
    if foto and entrega.prova_foto:
        raise ErroProva('A foto desta entrega já foi guardada.')
    if assinatura and entrega.prova_assinatura:
        raise ErroProva('A assinatura desta entrega já foi guardada.')
    if nome and entrega.recebido_por_nome:
        raise ErroProva('O nome de quem recebeu já foi guardado.')
    campos = ['prova_em']
    if foto:
        entrega.prova_foto.save(foto.name, foto, save=False)
        campos.append('prova_foto')
    if assinatura:
        entrega.prova_assinatura.save(assinatura.name, assinatura, save=False)
        campos.append('prova_assinatura')
    if nome:
        entrega.recebido_por_nome = nome
        campos.append('recebido_por_nome')
    entrega.prova_em = timezone.now()
    entrega.save(update_fields=campos)
