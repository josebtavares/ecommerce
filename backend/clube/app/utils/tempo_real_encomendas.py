"""
Tempo real das encomendas e entregas (como os reembolsos — utils/devolucoes.emitir — e as marcações —
servicos/tempo_real.py): quando uma encomenda ou a sua entrega mudam (estado, fatura anexada, condutor
atribuído/retirado, entregue, falhou…), avisa pelo WebSocket das notificações (grupo notif_<user>):

• o cliente (perfil → Encomendas);
• quem gere as encomendas ou as entregas da loja (dono, gestor, staff);
• o condutor da entrega — e também o anterior, quando a entrega lhe é retirada.

Só leva ids: a página aberta vai buscar o resto com as suas permissões. Depois do commit (antes disso a
página leria o estado antigo).
"""
from django.db import transaction
from django.db.models.signals import post_delete, post_init, post_save

ROLES_LOJA = ('dono', 'gestor', 'staff')        # gerir_encomendas / gerir_entregas (o condutor só vê as suas)


def _destinatarios(enc, condutores_extra=()):
    from ..models import Condutor, UtilizadorLoja
    ids = set(UtilizadorLoja.objects.filter(loja_id=enc.loja_id, ativo=True, role__in=ROLES_LOJA)
              .values_list('utilizador__user_id', flat=True))
    ids.add(enc.comprador.user_id)
    entrega = getattr(enc, 'entrega', None)
    condutores = set(condutores_extra)
    if entrega is not None and entrega.condutor_id:
        condutores.add(entrega.condutor_id)
    if condutores:
        ids |= set(Condutor.objects.filter(id__in=condutores).values_list('utilizador__user_id', flat=True))
    return ids


def _enviar(encomenda_id, condutores_extra=()):
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        from ..models import Encomenda
        enc = (Encomenda.objects.select_related('comprador', 'entrega').filter(pk=encomenda_id).first())
        if not enc:
            return
        camada = get_channel_layer()
        if camada is None:
            return
        evento = {'type': 'encomenda.atualizada', 'encomenda': {'id': enc.id, 'loja_id': enc.loja_id}}
        for uid in _destinatarios(enc, condutores_extra):
            async_to_sync(camada.group_send)(f'notif_{uid}', evento)
    except Exception:
        pass        # sem Redis/WebSocket: as páginas actualizam sozinhas de tempos a tempos


def emitir(encomenda_id, condutores_extra=()):
    """Avisa depois do commit (se a transacção for desfeita não se avisa). Uma acção com vários passos dá
    vários avisos seguidos — a página junta-os num só pedido (como nos reembolsos)."""
    if not encomenda_id:
        return
    extra = tuple(c for c in condutores_extra if c)
    transaction.on_commit(lambda: _enviar(encomenda_id, extra))


def _ao_iniciar_entrega(sender, instance, **kwargs):
    instance._condutor_original = instance.condutor_id


def _ao_gravar_encomenda(sender, instance, raw=False, **kwargs):
    if not raw:
        emitir(instance.pk)


def _ao_gravar_entrega(sender, instance, raw=False, **kwargs):
    if raw:
        return
    antes = getattr(instance, '_condutor_original', None)
    extra = (antes,) if antes and antes != instance.condutor_id else ()
    instance._condutor_original = instance.condutor_id
    emitir(instance.encomenda_id, extra)


def _ao_apagar_entrega(sender, instance, **kwargs):
    emitir(instance.encomenda_id, (instance.condutor_id,) if instance.condutor_id else ())


def ligar():
    from ..models import Encomenda, Entrega
    post_save.connect(_ao_gravar_encomenda, sender=Encomenda, weak=False, dispatch_uid='tempo_real_Encomenda')
    post_init.connect(_ao_iniciar_entrega, sender=Entrega, weak=False, dispatch_uid='tempo_real_Entrega_init')
    post_save.connect(_ao_gravar_entrega, sender=Entrega, weak=False, dispatch_uid='tempo_real_Entrega')
    post_delete.connect(_ao_apagar_entrega, sender=Entrega, weak=False, dispatch_uid='tempo_real_Entrega_apagar')
