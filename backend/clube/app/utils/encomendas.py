"""
Regras de encomendas partilhadas entre views e modelos.

  repor_stock(encomenda)               → devolve ao stock o que a encomenda reservou
                                         (o stock é descontado quando a encomenda é criada)
  cancelar_pendentes_da_loja(loja)     → cancela as encomendas ainda por pagar de uma loja
                                         que deixou de estar activa (fechada/suspensa)
"""
from django.db.models import F


def repor_stock(encomenda):
    """Repõe o stock de todos os itens (na variante, se a compra foi de uma)."""
    from ..models import Inventario, VarianteProduto
    from .variantes import atualizar_total_inventario

    from .conjuntos import repor as repor_conjunto

    produtos_variante = set()
    for item in encomenda.itens.select_related('produto', 'variante').all():
        if item.componentes:
            # conjunto: devolve o que se descontou de cada componente (snapshot da compra)
            repor_conjunto(item.componentes, item.quantidade)
            continue
        if not item.produto:
            continue
        if item.variante_id:
            VarianteProduto.objects.filter(id=item.variante_id).update(
                quantidade=F('quantidade') + item.quantidade
            )
            produtos_variante.add(item.produto)
        else:
            Inventario.objects.filter(produto=item.produto).update(
                quantidade=F('quantidade') + item.quantidade
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
