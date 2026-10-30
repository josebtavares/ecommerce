"""
Pagamento com cartão (vinti4) — contrato de cada loja com a SISP (models.AdesaoVinti4).

A SISP não tem pagamento dividido nem sub-comerciantes: a Bende não pode receber por conta das lojas
(contrato MD050.03, cláusula 4ª n.º 2). Cada loja adere em nome próprio (licença comercial em nome + NIF, ou
certidão comercial, + identificação de quem assina) e o dinheiro vai direto para a conta dela. A comissão da Bende
cobra-se à parte (fatura de comissões).

Percurso:
  1. a loja cumpre os requisitos (NIF, contactos email e telefone, localização, documentos aprovados);
  2. o dono vê os dados para a ficha de adesão (FROP020.01), entrega-a na SISP e marca "pedida";
  3. a SISP dá as credenciais; o dono põe-nas no backoffice (com a password) → por_validar;
  4. o admin (gerir_pagamentos) põe em testes e depois ativa; pode suspender. Mudar as credenciais volta a por_validar
     (uma conta trocada às escondidas desviava o dinheiro) — o dono recebe notificação e email.
Com pagamentos a sério (pagamentos.cobra_a_serio), só as lojas com a adesão ativa aceitam cartão (banco.online_suspenso).

A chave (posAutCode) é guardada cifrada (Fernet, settings.CHAVE_CREDENCIAIS ou derivada da SECRET_KEY) e nunca
sai do servidor. Nomes das credenciais provisórios até chegar o manual técnico da SISP.
"""
import base64
import hashlib
import logging
import re

from django.conf import settings
from django.db import transaction
from django.utils import timezone

log = logging.getLogger(__name__)

ESTADOS_COM_CARTAO = ('ativa',)
ACOES_ADMIN = {
    # acção: (estados de onde se pode, estado novo)
    'teste':     (('por_validar', 'suspensa'), 'teste'),
    'ativar':    (('por_validar', 'teste', 'suspensa'), 'ativa'),
    'suspender': (('teste', 'ativa'), 'suspensa'),
    'recusar':   (('por_validar',), 'pedida'),
}
_ID = re.compile(r'^[A-Za-z0-9_-]{1,40}$')


# ── cifra ────────────────────────────────────────────────────────

def _fernet():
    from cryptography.fernet import Fernet
    chave = getattr(settings, 'CHAVE_CREDENCIAIS', '') or ''
    if not chave:
        bruto = hashlib.sha256(('credenciais-lojas:' + settings.SECRET_KEY).encode()).digest()
        chave = base64.urlsafe_b64encode(bruto).decode()
    return Fernet(chave.encode() if isinstance(chave, str) else chave)


def cifrar(texto):
    return _fernet().encrypt(texto.encode()).decode()


def decifrar(cifrado):
    """Para o fornecedor SISP (quando existir). Nunca para respostas da API."""
    return _fernet().decrypt(cifrado.encode()).decode() if cifrado else ''


# ── estado ───────────────────────────────────────────────────────

def adesao(loja):
    from ..models import AdesaoVinti4
    return AdesaoVinti4.objects.filter(loja=loja).first()


def ativa(loja):
    from ..models import AdesaoVinti4
    return AdesaoVinti4.objects.filter(loja=loja, estado__in=ESTADOS_COM_CARTAO).exists()


def requisitos(loja):
    """O que a SISP pede antes de aderir (e o que a cláusula 3ª pede ao site)."""
    from .documentos_loja import verificada
    return [
        {'chave': 'nif', 'titulo': 'NIF da loja', 'ok': bool(re.fullmatch(r'\d{9}', loja.nif or '')),
         'ajuda': 'Configurações → Dados fiscais.'},
        {'chave': 'contactos', 'titulo': 'Email e telefone da loja (os dois)',
         'ok': bool((loja.contacto_email or '').strip() and (loja.contacto_telefone or '').strip()),
         'ajuda': 'A SISP exige os dois contactos de apoio ao cliente — Configurações → Contactos da loja.'},
        {'chave': 'localizacao', 'titulo': 'Morada da loja', 'ok': bool((loja.localizacao or '').strip()),
         'ajuda': 'Configurações → Informações.'},
        {'chave': 'documentos', 'titulo': 'Documentos aprovados (identificação + licença ou certidão comercial)',
         'ok': verificada(loja),
         'ajuda': 'Configurações → Documentos. São os mesmos que a SISP pede na adesão.'},
        {'chave': 'estado', 'titulo': 'Loja aberta', 'ok': loja.estado in ('ativa', 'pendente'),
         'ajuda': 'Uma loja suspensa ou fechada não pode aderir.'},
    ]


def ficha(loja):
    """Os dados da ficha de adesão da SISP (FROP020.01), já preenchidos com o que a Bende sabe."""
    from ..models import DadosBancarios
    from . import banco
    d = DadosBancarios.objects.filter(loja=loja).first()
    base = (getattr(settings, 'FRONTEND_BASE_URL', '') or 'https://bende.store').rstrip('/')
    dono = loja.dono
    nome_dono = ' '.join(x for x in (dono.user.first_name, dono.user.last_name) if x) or dono.user.username
    return [
        {'campo': 'Denominação / titular', 'valor': nome_dono},
        {'campo': 'NIF', 'valor': loja.nif or ''},
        {'campo': 'Morada', 'valor': loja.localizacao or ''},
        {'campo': 'Email', 'valor': loja.contacto_email or ''},
        {'campo': 'Telefone', 'valor': loja.contacto_telefone or ''},
        {'campo': 'URL do site', 'valor': f'{base}/loja/{loja.id}'},
        {'campo': 'Nome do estabelecimento', 'valor': loja.nome},
        {'campo': 'Tipo de atividade', 'valor': loja.categoria},
        {'campo': 'Mercadorias / serviços', 'valor': (loja.descricao or '')[:300]},
        {'campo': 'Modalidade', 'valor': 'Site próprio (loja na plataforma Bende)'},
        {'campo': 'Cartões', 'valor': 'vinti4 e internacionais'},
        {'campo': 'Banco de apoio', 'valor': f'{d.banco} — {banco.formatar_iban(d.nib)}' if d else ''},
        {'campo': 'Anexos', 'valor': 'Licença comercial (ou certidão comercial) e documento de identificação de quem assina'},
    ]


def payload(a, admin=False):
    if not a:
        return None
    out = {
        'estado': a.estado, 'estado_nome': a.get_estado_display(), 'motivo': a.motivo,
        'pos_id': a.pos_id, 'merchant_id': a.merchant_id, 'chave_definida': bool(a.chave_cifrada),
        'pedida_em': a.pedida_em.isoformat() if a.pedida_em else None,
        'credenciais_em': a.credenciais_em.isoformat() if a.credenciais_em else None,
        'decidido_em': a.decidido_em.isoformat() if a.decidido_em else None,
        'cartao': a.estado in ESTADOS_COM_CARTAO,
    }
    if admin:
        out['credenciais_por'] = a.credenciais_por.username if a.credenciais_por_id else ''
        out['decidido_por'] = a.decidido_por.username if a.decidido_por_id else ''
    return out


class ErroVinti4(Exception):
    pass


def _registar(loja, evento, a, extra=None):
    from .registo import registar
    registar('vinti4', evento, objeto_id=loja.id, loja_id=loja.id, estado_novo=a.estado,
             dados={'pos_id': a.pos_id, 'merchant_id': a.merchant_id, **(extra or {})})


def _avisar_admins(loja, titulo, mensagem):
    try:
        from ..models import Notificacao, Utilizador
        admins = [u for u in Utilizador.objects.filter(user__is_staff=True, user__is_active=True).select_related('user')
                  if u.pode_admin('gerir_pagamentos')]
        Notificacao.objects.bulk_create([Notificacao(utilizador=u, tipo='vinti4', titulo=titulo, mensagem=mensagem,
                                                     loja=loja, link=f'/admin/lojas/{loja.id}') for u in admins])
    except Exception:          # o pedido já está gravado: o aviso não pode estragar a resposta
        log.exception('vinti4: aviso aos admins falhou')


def _avisar_dono(loja, titulo, mensagem, email=False):
    from ..Views.notificacaoView import notificar
    try:
        notificar(loja.dono, 'vinti4', titulo, mensagem, loja=loja, link=f'/loja/{loja.id}/backoffice/configuracoes')
    except Exception:
        log.exception('vinti4: aviso ao dono falhou')
    para = loja.dono.user.email
    if email and para:
        def enviar():
            from .email_html import criar
            try:
                criar(para, f'{titulo} — {loja.nome}', mensagem).send(fail_silently=False)
            except Exception:
                log.exception('vinti4: email ao dono falhou')
        transaction.on_commit(enviar)


def _bloquear(loja):
    from ..models import AdesaoVinti4, Loja
    Loja.objects.select_for_update().filter(pk=loja.pk).first()
    return AdesaoVinti4.objects.filter(loja=loja).first()


def pedir(loja):
    """O dono entregou a ficha na SISP."""
    from ..models import AdesaoVinti4
    falta = [r['titulo'] for r in requisitos(loja) if not r['ok']]
    if falta:
        raise ErroVinti4('Antes de pedir a adesão falta: ' + '; '.join(falta) + '.')
    with transaction.atomic():
        a = _bloquear(loja)
        if a:
            raise ErroVinti4('A adesão já foi pedida.')
        a = AdesaoVinti4.objects.create(loja=loja, estado='pedida')
        _registar(loja, 'pedida', a)
    return a


def guardar_credenciais(request, loja, pos_id, merchant_id, chave):
    pos_id, merchant_id, chave = (str(x or '').strip() for x in (pos_id, merchant_id, chave))
    erros = {}
    if not _ID.match(pos_id):
        erros['pos_id'] = 'O POS ID tem só letras, números, - ou _ (até 40).'
    if not _ID.match(merchant_id):
        erros['merchant_id'] = 'O Merchant ID tem só letras, números, - ou _ (até 40).'
    if not 4 <= len(chave) <= 200 or any(c.isspace() for c in chave):
        erros['chave'] = 'Cola a chave (posAutCode) tal como a SISP a enviou.'
    if erros:
        return None, erros
    with transaction.atomic():
        a = _bloquear(loja)
        if not a:
            raise ErroVinti4('Primeiro marca a adesão como pedida.')
        antes = a.estado
        a.pos_id, a.merchant_id, a.chave_cifrada = pos_id, merchant_id, cifrar(chave)
        a.estado, a.motivo = 'por_validar', ''
        a.credenciais_em, a.credenciais_por = timezone.now(), request.user
        a.save()
        _registar(loja, 'credenciais', a, {'estado_anterior': antes})
        from .horarios import fuso
        quando = timezone.now().astimezone(fuso()).strftime('%d/%m/%Y %H:%M')
        texto = (f'As credenciais vinti4 da loja "{loja.nome}" foram alteradas por {request.user.username} em {quando} '
                 f'(POS ID {pos_id}). O pagamento com cartão fica parado até a Bende as validar. '
                 'Se não foste tu, muda a tua password e contacta o suporte.')
        _avisar_dono(loja, 'Credenciais vinti4 alteradas', texto, email=True)
        _avisar_admins(loja, 'Credenciais vinti4 para validar', f'A loja "{loja.nome}" enviou as credenciais vinti4.')
    return a, None


def decidir(request, loja, acao, motivo=''):
    motivo = ' '.join(str(motivo or '').split())[:300]
    if acao not in ACOES_ADMIN:
        raise ErroVinti4('Acção inválida.')
    if acao in ('suspender', 'recusar') and len(motivo) < 5:
        raise ErroVinti4('Escreve o motivo (a loja vê-o).')
    de, para = ACOES_ADMIN[acao]
    with transaction.atomic():
        a = _bloquear(loja)
        if not a or a.estado not in de:
            raise ErroVinti4('Não é possível neste estado.')
        if para in ('teste', 'ativa') and not (a.pos_id and a.merchant_id and a.chave_cifrada):
            raise ErroVinti4('Faltam as credenciais.')
        antes = a.estado
        a.estado, a.motivo = para, motivo
        a.decidido_em, a.decidido_por = timezone.now(), request.user
        a.save()
        _registar(loja, acao, a, {'estado_anterior': antes, 'motivo': motivo})
        textos = {
            'teste':     ('Cartão vinti4 em testes', 'A Bende está a testar o pagamento com cartão da tua loja com a SISP.'),
            'ativar':    ('Cartão vinti4 ativo', 'A tua loja já aceita pagamentos com cartão. O dinheiro vai direto para a '
                                                 'conta do teu contrato vinti4.'),
            'suspender': ('Cartão vinti4 suspenso', f'O pagamento com cartão da tua loja foi suspenso: {motivo}'),
            'recusar':   ('Credenciais vinti4 recusadas', f'As credenciais vinti4 não foram aceites: {motivo}. '
                                                          'Corrige-as em Configurações.'),
        }
        _avisar_dono(loja, *textos[acao])
    return a
