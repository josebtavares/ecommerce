"""
Emails com os documentos de cada pagamento (PDF anexado + link para o site):
- ao cliente: comprovativo quando a encomenda é paga; fatura quando a loja a regista;
- ao dono da loja/POS: comprovativo da mensalidade paga; fatura do Bende (mensalidade e comissões do mês).

Os comprovativos saem sozinhos (signals em ligar(): qualquer caminho que aprove um pagamento passa
por aqui) e só uma vez (comprovativo_enviado_em). Uma falha no envio nunca desfaz o pagamento:
fica no log (Sentry).
"""
import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models.signals import post_save
from django.utils import timezone

from . import documentos

log = logging.getLogger(__name__)


def _link(caminho):
    return f'{settings.FRONTEND_BASE_URL}{caminho}'


def _enviar(para, assunto, texto, anexos=()):
    if not para:
        return False
    try:
        msg = EmailMessage(subject=assunto, body=texto + '\n\nBende', from_email=settings.DEFAULT_FROM_EMAIL, to=[para])
        for nome, conteudo in anexos:
            msg.attach(nome, conteudo, 'application/pdf')
        msg.send()
        return True
    except Exception:
        log.exception('email fiscal: falhou "%s" para utilizador', assunto)
        return False


def _pdf_registado(ficheiro):
    """O PDF da fatura que alguém carregou (pode não haver)."""
    if not ficheiro:
        return None
    try:
        with ficheiro.open('rb') as f:
            return f.read()
    except Exception:
        log.exception('email fiscal: não consegui ler %s', ficheiro.name)
        return None


def _dono_email(alvo):
    try:
        return alvo.dono.user.email
    except Exception:
        return ''


def _reservar(modelo, pk):
    """Marca o comprovativo como enviado antes de enviar — dois saves seguidos não mandam dois emails."""
    return modelo.objects.filter(pk=pk, comprovativo_enviado_em=None).update(comprovativo_enviado_em=timezone.now()) == 1


def _libertar(modelo, pk):
    modelo.objects.filter(pk=pk).update(comprovativo_enviado_em=None)


def _caminho_alvo(alvo, loja_id):
    return f'/loja/{loja_id}/backoffice?seccao=subscricao' if loja_id else '/pos/dashboard'


# ── Encomendas ─────────────────────────────────────────────────

def enviar_comprovativo_encomenda(enc):
    if not _reservar(type(enc), enc.pk):
        return
    user = enc.comprador.user
    ok = _enviar(
        user.email, f'Comprovativo de pagamento — encomenda #{enc.id} ({enc.loja.nome})',
        f'Olá {user.first_name or user.username},\n\n'
        f'O pagamento da tua encomenda #{enc.id} em {enc.loja.nome} foi confirmado. '
        f'Segue em anexo o comprovativo.\n\nA fatura é emitida pela loja e também te chega por email '
        f'quando estiver disponível. Podes ver a encomenda aqui: {_link("/perfil")}',
        [(documentos.nome_comprovativo_encomenda(enc), documentos.pdf_comprovativo_encomenda(enc))])
    if not ok:
        _libertar(type(enc), enc.pk)


def enviar_fatura_encomenda(enc):
    user = enc.comprador.user
    pdf = _pdf_registado(enc.fatura_pdf)
    _enviar(
        user.email, f'Fatura {enc.fatura_numero} — encomenda #{enc.id} ({enc.loja.nome})',
        f'Olá {user.first_name or user.username},\n\n'
        f'{enc.loja.nome} emitiu a fatura {enc.fatura_numero} da tua encomenda #{enc.id}.'
        + (' Segue em anexo.' if pdf else '') + f'\n\nTambém a encontras na encomenda: {_link("/perfil")}',
        [(f'fatura-encomenda-{enc.id}.pdf', pdf)] if pdf else [])


def _ao_gravar_pagamento(sender, instance, **kwargs):
    if instance.status != 'aprovado':
        return
    enc = instance.encomenda
    if enc.comprovativo_enviado_em:
        return
    # depois do commit: o pagamento pode ainda ser desfeito; e a encomenda já tem tudo gravado
    transaction.on_commit(lambda: enviar_comprovativo_encomenda(type(enc).objects.select_related(
        'loja', 'comprador__user', 'pagamento__metodo').get(pk=enc.pk)))


# ── Subscrições e comissões (o Bende cobra às lojas/POS) ──────

def enviar_comprovativo_subscricao(f):
    from .subscricoes import nome_alvo
    if not _reservar(type(f), f.pk):
        return
    alvo = f.alvo
    ok = _enviar(
        _dono_email(alvo), f'Comprovativo de pagamento — {f.descricao}',
        f'Olá,\n\nRecebemos o pagamento da mensalidade "{f.descricao}" de {nome_alvo(alvo)}. '
        f'Segue em anexo o comprovativo.\n\nA fatura do Bende chega-te por email quando for emitida. '
        f'Subscrição: {_link(_caminho_alvo(alvo, f.loja_id))}',
        [(documentos.nome_comprovativo_subscricao(f), documentos.pdf_comprovativo_subscricao(f))])
    if not ok:
        _libertar(type(f), f.pk)


def enviar_fatura_subscricao(f):
    from .subscricoes import nome_alvo
    alvo = f.alvo
    pdf = _pdf_registado(f.fatura_pdf)
    _enviar(
        _dono_email(alvo), f'Fatura {f.fatura_numero} — {f.descricao}',
        f'Olá,\n\nO Bende emitiu a fatura {f.fatura_numero} da mensalidade "{f.descricao}" de {nome_alvo(alvo)}.'
        + (' Segue em anexo.' if pdf else '') + f'\n\nSubscrição: {_link(_caminho_alvo(alvo, f.loja_id))}',
        [(f'fatura-subscricao-{f.id}.pdf', pdf)] if pdf else [])


def enviar_fatura_comissoes(fc):
    loja = fc.loja
    pdf = _pdf_registado(fc.fatura_pdf)
    anexos = [(documentos.nome_extrato_comissoes(loja, fc.mes), documentos.pdf_extrato_comissoes(loja, fc.mes))]
    if pdf:
        anexos.insert(0, (f'fatura-comissoes-{loja.id}-{fc.mes:%Y-%m}.pdf', pdf))
    _enviar(
        _dono_email(loja), f'Fatura {fc.fatura_numero} — comissões de {fc.mes:%m/%Y} ({loja.nome})',
        f'Olá,\n\nO Bende emitiu a fatura {fc.fatura_numero} das comissões de {fc.mes:%m/%Y} da loja {loja.nome}. '
        f'Seguem em anexo a fatura{"" if pdf else " (sem PDF)"} e o extrato das comissões.\n\n'
        f'Backoffice: {_link(f"/loja/{loja.id}/backoffice?seccao=subscricao")}',
        anexos)


def enviar_fatura_anulada(obj, numero, motivo):
    """A fatura deixou de valer (anulada com motivo): quem a recebeu por email fica a saber."""
    from .subscricoes import nome_alvo
    nome = obj._meta.model_name
    if nome == 'encomenda':
        user = obj.comprador.user
        para, assunto = user.email, f'Fatura {numero} anulada — encomenda #{obj.id} ({obj.loja.nome})'
        texto = (f'Olá {user.first_name or user.username},\n\n{obj.loja.nome} anulou a fatura {numero} da tua encomenda '
                 f'#{obj.id}. Motivo: {motivo}\n\nSe a loja emitir outra, recebes-a por email. Encomenda: {_link("/perfil")}')
    elif nome == 'faturasubscricao':
        alvo = obj.alvo
        para, assunto = _dono_email(alvo), f'Fatura {numero} anulada — {obj.descricao}'
        texto = (f'Olá,\n\nO Bende anulou a fatura {numero} da mensalidade "{obj.descricao}" de {nome_alvo(alvo)}. '
                 f'Motivo: {motivo}\n\nSubscrição: {_link(_caminho_alvo(alvo, obj.loja_id))}')
    else:
        loja = obj.loja
        para, assunto = _dono_email(loja), f'Fatura {numero} anulada — comissões de {obj.mes:%m/%Y} ({loja.nome})'
        texto = (f'Olá,\n\nO Bende anulou a fatura {numero} das comissões de {obj.mes:%m/%Y} da loja {loja.nome}. '
                 f'Motivo: {motivo}\n\nBackoffice: {_link(f"/loja/{loja.id}/backoffice?seccao=subscricao")}')
    _enviar(para, assunto, texto)


def _ao_gravar_fatura_subscricao(sender, instance, **kwargs):
    # mensalidades oferecidas (valor 0) não levam comprovativo
    if instance.estado != 'paga' or instance.comprovativo_enviado_em or not instance.valor:
        return
    pk = instance.pk
    transaction.on_commit(lambda: enviar_comprovativo_subscricao(
        type(instance).objects.select_related('loja__dono__user', 'pos__dono__user').get(pk=pk)))


def ligar():
    """Chamado em AppConfig.ready()."""
    from ..models import FaturaSubscricao, Pagamento
    post_save.connect(_ao_gravar_pagamento, sender=Pagamento, weak=False, dispatch_uid='fiscal_comprovativo_encomenda')
    post_save.connect(_ao_gravar_fatura_subscricao, sender=FaturaSubscricao, weak=False,
                      dispatch_uid='fiscal_comprovativo_subscricao')
