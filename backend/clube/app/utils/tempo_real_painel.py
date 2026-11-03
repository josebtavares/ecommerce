"""
Tempo real do Dashboard e dos Relatórios do admin: quando muda alguma coisa que conta para os números da plataforma
— uma venda (encomenda paga/concluída/cancelada, conta do POS fechada, marcação concluída), um pagamento, um
reembolso, uma comissão, um crédito ou uma cobrança de comissões, uma mensalidade ou uma subscrição —, avisa os
admins que vêem as estatísticas ou os relatórios (ver_stats, ver_relatorios) pelo WebSocket das notificações.

Só diz de onde veio ({origem}); a página espera um pouco (juntam-se vários avisos seguidos) e recarrega em silêncio.
Depois do commit (transacção desfeita → não avisa).
"""
from django.db import transaction
from django.db.models.signals import post_save

PERMISSOES_ADMIN = ('ver_stats', 'ver_relatorios', 'gerir_pagamentos')   # + Admin → Pagamentos


def _destinatarios():
    from ..models import Utilizador
    roles = [k for k, v in Utilizador.PERMISSOES_ADMIN.items() if any(p in v for p in PERMISSOES_ADMIN)]
    return set(Utilizador.objects.filter(user__is_staff=True, role_admin__in=roles).values_list('user_id', flat=True))


def _enviar(origem):
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        camada = get_channel_layer()
        if camada is None:
            return
        evento = {'type': 'painel.atualizado', 'painel': {'origem': origem}}
        for uid in _destinatarios():
            async_to_sync(camada.group_send)(f'notif_{uid}', evento)
    except Exception:
        pass        # sem Redis/WebSocket: as páginas verificam sozinhas de tempos a tempos


def emitir(origem):
    transaction.on_commit(lambda: _enviar(origem))


def _ao_gravar(origem, so_estado=None):
    """so_estado: só quando muda este campo (o Pagamento e o Reembolso gravam-se muitas vezes)."""
    def gravar(sender, instance, created=False, raw=False, update_fields=None, **kwargs):
        if raw or getattr(instance, '_sem_tempo_real', False):
            return
        if so_estado and not created and update_fields is not None and so_estado not in update_fields:
            return
        emitir(origem)
    return gravar


def ligar():
    from ..models import (CobrancaComissoes, Comissao, CreditoComissao, FaturaSubscricao, Pagamento, Reembolso,
                          Subscricao)
    for origem, modelo, campo in (('comissao', Comissao, None), ('credito_comissao', CreditoComissao, None),
                                  ('cobranca_comissoes', CobrancaComissoes, 'estado'),
                                  ('mensalidade', FaturaSubscricao, 'estado'), ('subscricao', Subscricao, None),
                                  ('pagamento', Pagamento, 'status'), ('reembolso', Reembolso, 'estado')):
        post_save.connect(_ao_gravar(origem, campo), sender=modelo, weak=False, dispatch_uid=f'painel_{modelo.__name__}')
    # as vendas (encomendas, contas do POS, marcações) avisam pelo tempo real da faturação, que só dispara quando
    # muda o que conta (estado, valor) — utils/tempo_real_faturacao.py chama emitir()
