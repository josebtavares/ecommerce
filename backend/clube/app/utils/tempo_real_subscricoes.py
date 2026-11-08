"""
Tempo real das mensalidades e das faturas do Bende (como utils/tempo_real_encomendas.py): quando uma mensalidade
(FaturaSubscricao) muda — emitida, paga, adiada, anulada, fatura do Bende registada/substituída/anulada —, quando
uma subscrição muda de estado ou de plano, ou quando a fatura das comissões de um mês (FaturaComissoes) é
registada/anulada, e nas comissões — uma comissão registada/recalculada/anulada/liquidada, um crédito de reembolso,
uma cobrança mensal emitida/paga/anulada —, avisa pelo WebSocket das notificações (grupo notif_<user>):

• os admins que gerem subscrições, faturação ou pagamentos (Admin → Subscrições, Faturação e Comissões);
• quem vê a subscrição da loja (Backoffice → Subscrição: dono, gestor, contabilista…);
• o dono do POS (a página do POS não tem WebSocket: verifica sozinha de tempos a tempos).

Só leva ids: a página aberta vai buscar o resto com as suas permissões. Depois do commit.
"""
from django.db import transaction
from django.db.models.signals import post_delete, post_save

PERMISSOES_ADMIN = ('gerir_subscricoes', 'gerir_faturacao', 'gerir_pagamentos')


def _destinatarios(loja_id, pos_id):
    from ..models import Utilizador, UtilizadorLoja
    roles_admin = [k for k, v in Utilizador.PERMISSOES_ADMIN.items() if any(p in v for p in PERMISSOES_ADMIN)]
    ids = set(Utilizador.objects.filter(user__is_staff=True, role_admin__in=roles_admin)
              .values_list('user_id', flat=True))
    if loja_id:
        roles = [k for k, v in UtilizadorLoja.PERMISSOES.items() if 'ver_subscricao' in v]
        ids |= set(UtilizadorLoja.objects.filter(loja_id=loja_id, ativo=True, role__in=roles)
                   .values_list('utilizador__user_id', flat=True))
    if pos_id:
        from ..pos.models import ConfiguracaoPOS
        dono = ConfiguracaoPOS.objects.filter(pk=pos_id).values_list('dono__user_id', flat=True).first()
        if dono:
            ids.add(dono)
    ids.discard(None)
    return ids


def _enviar(aviso):
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        camada = get_channel_layer()
        if camada is None:
            return
        evento = {'type': 'subscricao.atualizada', 'subscricao': aviso}
        for uid in _destinatarios(aviso.get('loja_id'), aviso.get('pos_id')):
            async_to_sync(camada.group_send)(f'notif_{uid}', evento)
        # quem está no POS (dono e equipa) — utils/tempo_real_pos.py; o plano "Loja + POS" é da loja: avisa os
        # POS ligados a ela (só nas mensalidades e subscrições — as comissões não são do POS)
        from . import tempo_real_pos
        pos_ids = [aviso['pos_id']] if aviso.get('pos_id') else (
            tempo_real_pos._pos_da_loja(aviso['loja_id']) if aviso.get('tipo') in ('mensalidade', 'subscricao') else [])
        for pid in pos_ids:
            tempo_real_pos._enviar(pid, [{'tipo': 'subscricao', 'id': aviso.get('id'), 'pos_id': pid}])
    except Exception:
        pass        # sem Redis/WebSocket: as páginas actualizam sozinhas de tempos a tempos


def emitir(tipo, id_, loja_id=None, pos_id=None):
    """tipo: 'mensalidade' | 'subscricao' | 'fatura_comissoes' | 'comissao' | 'credito_comissao' |
    'cobranca_comissoes'. Avisa depois do commit (desfeita → não avisa)."""
    if not (loja_id or pos_id):
        return
    aviso = {'tipo': tipo, 'id': id_, 'loja_id': loja_id, 'pos_id': pos_id}
    transaction.on_commit(lambda: _enviar(aviso))


def _ao_gravar_mensalidade(sender, instance, raw=False, **kwargs):
    if not raw:
        emitir('mensalidade', instance.pk, instance.loja_id, instance.pos_id)


def _ao_gravar_subscricao(sender, instance, raw=False, **kwargs):
    if not raw:
        emitir('subscricao', instance.pk, instance.loja_id or instance.loja_servicos_id, instance.pos_id)


def _ao_mudar_fatura_comissoes(sender, instance, raw=False, **kwargs):
    if not raw:
        emitir('fatura_comissoes', instance.pk, instance.loja_id)


def _ao_gravar_comissoes(tipo):
    def gravar(sender, instance, raw=False, **kwargs):
        # pagar/anular uma cobrança grava muitas comissões de uma vez: avisa só a cobrança (_sem_tempo_real)
        if not raw and not getattr(instance, '_sem_tempo_real', False):
            emitir(tipo, instance.pk, instance.loja_id)
    return gravar


def ligar():
    from ..models import CobrancaComissoes, Comissao, CreditoComissao, FaturaComissoes, FaturaSubscricao, Subscricao
    for tipo, modelo in (('comissao', Comissao), ('credito_comissao', CreditoComissao),
                         ('cobranca_comissoes', CobrancaComissoes)):
        post_save.connect(_ao_gravar_comissoes(tipo), sender=modelo, weak=False, dispatch_uid=f'tempo_real_{modelo.__name__}')
    post_save.connect(_ao_gravar_mensalidade, sender=FaturaSubscricao, weak=False, dispatch_uid='tempo_real_FaturaSubscricao')
    post_save.connect(_ao_gravar_subscricao, sender=Subscricao, weak=False, dispatch_uid='tempo_real_Subscricao')
    post_save.connect(_ao_mudar_fatura_comissoes, sender=FaturaComissoes, weak=False, dispatch_uid='tempo_real_FaturaComissoes')
    # anular a fatura das comissões apaga a linha (utils/fiscal.anular_fatura)
    post_delete.connect(_ao_mudar_fatura_comissoes, sender=FaturaComissoes, weak=False,
                        dispatch_uid='tempo_real_FaturaComissoes_apagar')
