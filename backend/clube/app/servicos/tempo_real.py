"""
Tempo real das marcações (como os reembolsos — utils/devolucoes.emitir): quando uma marcação, uma
mensagem da conversa ou uma proposta de preço mudam, avisa pelo WebSocket das notificações
(grupo notif_<user>) o cliente, quem gere as marcações da loja e o profissional com conta.
Só leva ids: a página aberta vai buscar o resto com as suas permissões. Depois do commit.
"""
from django.db import transaction
from django.db.models.signals import post_save

ROLES_LOJA = ('dono', 'gestor', 'staff')        # gerir_marcacoes


def _destinatarios(m):
    from ..models import UtilizadorLoja
    ids = set(UtilizadorLoja.objects.filter(loja_id=m.loja_id, ativo=True, role__in=ROLES_LOJA)
              .values_list('utilizador__user_id', flat=True))
    if m.cliente_id:
        ids.add(m.cliente.user_id)
    prof = m.profissional
    if prof.membro_id and prof.membro.ativo:
        ids.add(prof.membro.utilizador.user_id)
    return ids


def _enviar(marcacao_id):
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        from .models import Marcacao
        m = Marcacao.objects.select_related('cliente', 'profissional__membro__utilizador').filter(pk=marcacao_id).first()
        if not m:
            return
        camada = get_channel_layer()
        evento = {'type': 'marcacao.atualizada', 'marcacao': {'id': m.id, 'loja_id': m.loja_id}}
        for uid in _destinatarios(m):
            async_to_sync(camada.group_send)(f'notif_{uid}', evento)
    except Exception:
        pass        # sem Redis/WebSocket: as páginas actualizam sozinhas de tempos a tempos


def emitir(marcacao_id):
    transaction.on_commit(lambda: _enviar(marcacao_id))


def _ao_gravar(sender, instance, raw=False, **kwargs):
    if raw:
        return
    emitir(instance.pk if sender.__name__ == 'Marcacao' else instance.marcacao_id)


def ligar():
    from .models import Marcacao, MensagemMarcacao, PropostaPreco
    for modelo in (Marcacao, MensagemMarcacao, PropostaPreco):
        post_save.connect(_ao_gravar, sender=modelo, weak=False, dispatch_uid=f'tempo_real_{modelo.__name__}')
