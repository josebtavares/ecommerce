"""
Regras de encomendas partilhadas entre views e modelos.

  repor_stock(encomenda, quantidades)  → devolve ao stock o que a encomenda reservou (ou parte)
                                         (o stock é descontado quando a encomenda é criada)
  cancelar_pendentes_da_loja(loja)     → cancela as encomendas ainda por pagar de uma loja
                                         que deixou de estar activa (fechada/suspensa)
  expirar_por_pagar()                  → worker: cancela as por pagar há mais de 30 min (repõe stock)
  cancelar_anteriores_por_pagar(u, l)  → nova encomenda do mesmo cliente na mesma loja substitui as por pagar
"""
from django.db.models import F


def repor_stock(encomenda, quantidades=None):
    """
    Repõe o stock de todos os itens (na variante, se a compra foi de uma).
    quantidades={item_id: qtd} → só essas unidades (devolução de parte da encomenda).
    """
    from ..models import Inventario, VarianteProduto
    from .variantes import atualizar_total_inventario

    from .conjuntos import repor as repor_conjunto

    produtos_variante = set()
    for item in encomenda.itens.select_related('produto', 'variante').all():
        qtd = item.quantidade if quantidades is None else min(quantidades.get(item.id, 0), item.quantidade)
        if qtd <= 0:
            continue
        if item.componentes:
            # conjunto: devolve o que se descontou de cada componente (snapshot da compra)
            repor_conjunto(item.componentes, qtd)
            continue
        if not item.produto:
            continue
        if item.variante_id:
            VarianteProduto.objects.filter(id=item.variante_id).update(
                quantidade=F('quantidade') + qtd
            )
            produtos_variante.add(item.produto)
        elif item.produto.stock_por_variante:
            # a variante comprada foi apagada depois: não há onde repor (somar ao total do produto
            # deixava o inventário diferente da soma das variantes)
            produtos_variante.add(item.produto)
        else:
            Inventario.objects.filter(produto=item.produto).update(
                quantidade=F('quantidade') + qtd
            )
    for produto in produtos_variante:
        atualizar_total_inventario(produto)


_MOTIVO_CLIENTE = {
    'fechada':  'A loja "{loja}" fechou temporariamente',
    'suspensa': 'A loja "{loja}" deixou de estar disponível',
}


def cancelar_pendentes_da_loja(loja):
    """
    Uma loja que deixa de estar activa não pode receber pagamentos, por isso as encomendas
    ainda por pagar (status 'pendente') ficavam presas para sempre. Cancela-as, repõe o stock
    e avisa o comprador. As já pagas não mudam — continuam a ser geridas no backoffice.
    Chamar dentro de uma transacção (Loja.mudar_estado). Devolve quantas cancelou.
    """
    from ..models import Encomenda
    from ..Views.notificacaoView import notificar

    pendentes = list(
        Encomenda.objects.select_for_update()
        .filter(loja=loja, status='pendente')
        .select_related('comprador')
    )
    motivo = _MOTIVO_CLIENTE.get(loja.estado, 'A loja "{loja}" não está disponível').format(loja=loja.nome)
    for encomenda in pendentes:
        encomenda.status = 'cancelado'
        encomenda.save(update_fields=['status'])
        repor_stock(encomenda)
        notificar(
            utilizador=encomenda.comprador,
            tipo='encomenda_cancelada',
            titulo=f'Encomenda cancelada #{encomenda.id}',
            mensagem=f'{motivo} e a tua encomenda, que ainda não estava paga, foi cancelada. '
                     f'Não foi cobrado nada.',
            loja=loja,
            link='/perfil',
        )
    return len(pendentes)


# ── Encomendas por pagar: prazo para pagar ───────────────────────────
# O stock é descontado quando a encomenda é criada; se o pagamento falha ou o cliente desiste,
# a encomenda ficava 'pendente' para sempre a prender o stock. Agora tem um prazo.

PRAZO_PAGAMENTO_MIN = 30
AVISAR_ATE_HORAS = 24      # encomendas por pagar mais antigas (de antes desta regra) cancelam-se sem avisar


def prazo_pagamento(encomenda):
    from datetime import timedelta
    return encomenda.data_criacao + timedelta(minutes=PRAZO_PAGAMENTO_MIN)


def pagamento_expirado(encomenda, agora=None):
    from django.utils import timezone
    return encomenda.status == 'pendente' and (agora or timezone.now()) >= prazo_pagamento(encomenda)


def _cancelar_por_pagar(encomenda, mensagem_cliente=None, avisar_loja=True):
    """Cancela uma encomenda por pagar (já bloqueada com select_for_update) e repõe o stock."""
    from ..Views.notificacaoView import notificar, notificar_staff
    encomenda.status = 'cancelado'
    encomenda.save(update_fields=['status'])
    repor_stock(encomenda)
    if mensagem_cliente:
        notificar(utilizador=encomenda.comprador, tipo='encomenda_cancelada',
                  titulo=f'Encomenda cancelada #{encomenda.id}', mensagem=mensagem_cliente,
                  loja=encomenda.loja, link='/perfil')
    if avisar_loja:
        notificar_staff(loja=encomenda.loja, roles=['dono', 'gestor', 'staff'], tipo='encomenda_cancelada_loja',
                        titulo=f'Encomenda #{encomenda.id} cancelada',
                        mensagem='O pagamento não foi concluído a tempo. Stock reposto automaticamente.',
                        link=f'/loja/{encomenda.loja_id}/backoffice')


MSG_EXPIROU = ('O pagamento não foi concluído em {min} minutos e a encomenda foi cancelada. '
               'Não foi cobrado nada — os produtos continuam no teu carrinho se quiseres tentar de novo.')


def expirar_encomenda(encomenda, agora=None):
    """Se já passou o prazo, cancela-a (a encomenda tem de vir com select_for_update). → True se cancelou."""
    from datetime import timedelta
    from django.utils import timezone
    agora = agora or timezone.now()
    if not pagamento_expirado(encomenda, agora):
        return False
    recente = encomenda.data_criacao >= agora - timedelta(hours=AVISAR_ATE_HORAS)
    _cancelar_por_pagar(encomenda, MSG_EXPIROU.format(min=PRAZO_PAGAMENTO_MIN) if recente else None,
                        avisar_loja=recente)
    return True


def expirar_por_pagar(agora=None, lote=200):
    """
    Worker (a cada minuto): cancela as encomendas por pagar há mais de PRAZO_PAGAMENTO_MIN minutos
    e repõe o stock. skip_locked: uma encomenda a ser paga neste momento fica para a volta seguinte
    (e se o pagamento passar, já não está 'pendente'). Devolve quantas cancelou.
    """
    from datetime import timedelta
    from django.db import transaction
    from django.utils import timezone
    from ..models import Encomenda
    agora = agora or timezone.now()
    limite = agora - timedelta(minutes=PRAZO_PAGAMENTO_MIN)
    n = 0
    with transaction.atomic():
        for e in (Encomenda.objects.select_for_update(skip_locked=True, of=('self',))
                  .filter(status='pendente', data_criacao__lt=limite)
                  .select_related('comprador', 'loja').order_by('id')[:lote]):
            n += expirar_encomenda(e, agora)
    return n


def cancelar_anteriores_por_pagar(utilizador, loja):
    """
    O cliente volta a encomendar na mesma loja (o pagamento anterior falhou ou desistiu): as
    encomendas dele ainda por pagar nessa loja são substituídas pela nova — cancela-as e devolve
    o stock antes de validar o da nova (senão a última unidade ficava presa na encomenda antiga).
    Sem avisos: é o próprio cliente que está a refazer a encomenda.
    """
    from ..models import Encomenda
    antigas = list(Encomenda.objects.select_for_update()
                   .filter(comprador=utilizador, loja=loja, status='pendente').order_by('id'))
    for e in antigas:
        _cancelar_por_pagar(e, None, avisar_loja=False)
    return len(antigas)
