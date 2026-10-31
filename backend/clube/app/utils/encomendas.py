"""
Regras de encomendas partilhadas entre views e modelos.

  repor_stock(encomenda, quantidades)  → devolve ao stock o que a encomenda reservou (ou parte)
                                         (o stock é descontado quando a encomenda é criada)
  cancelar_pendentes_da_loja(loja)     → cancela as encomendas ainda por pagar de uma loja
                                         que deixou de estar activa (fechada/suspensa)
  expirar_por_pagar()                  → worker: cancela as por pagar há mais de 30 min (repõe stock)
  valor_a_cobrar(encomenda)            → o que o condutor recebe em dinheiro na entrega (ou None)
  transferencia_por_confirmar(enc)     → paga por transferência que a loja ainda não viu chegar: não sai
  confirmar_transferencia(encomenda)   → a loja viu o dinheiro: pagamento aprovado + comissão
  aprovar_dinheiro(encomenda)          → entregue/concluída: o dinheiro foi recebido, pagamento + comissão
  cancelar_entrega(encomenda)          → encomenda cancelada: termina a entrega e avisa o condutor
  fechar_entrega(encomenda)            → a loja concluiu a encomenda: a entrega em curso fica entregue
  libertar_entregas(condutor, nota)    → o condutor saiu: as entregas dele voltam à loja para reatribuir
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


def transferencia_por_confirmar(encomenda):
    """
    Transferência à espera de a loja a ver chegar. A referência não distingue (é 'dinheiro' em todo o pagamento
    offline, pagamentos/servico.py): é o método que diz. A encomenda não sai sem isto resolvido.
    """
    p = getattr(encomenda, 'pagamento', None)
    return bool(p and p.status == 'pendente' and p.metodo_id and p.metodo.tipo == 'transferencia')


def _em_dinheiro_por_receber(encomenda):
    p = getattr(encomenda, 'pagamento', None)
    if p and p.status == 'pendente' and p.referencia_transacao == 'dinheiro' and not transferencia_por_confirmar(encomenda):
        return p
    return None


def valor_a_cobrar(encomenda):
    """Dinheiro a receber do cliente na entrega (já sem os esgotados); None se não há nada a cobrar."""
    p = _em_dinheiro_por_receber(encomenda)
    return p.valor if p else None


def _aprovar(encomenda, pagamento):
    from ..models import Comissao
    pagamento.status = 'aprovado'
    pagamento.save(update_fields=['status'])
    Comissao.registar(encomenda)


def aprovar_dinheiro(encomenda):
    """Entregue/concluída: o dinheiro foi recebido → pagamento aprovado + comissão. True se foi agora."""
    p = _em_dinheiro_por_receber(encomenda)
    if not p:
        return False
    _aprovar(encomenda, p)
    return True


def confirmar_transferencia(encomenda):
    """A loja viu a transferência na conta (encomenda bloqueada por quem chama)."""
    _aprovar(encomenda, encomenda.pagamento)


ENTREGA_EM_CURSO = ('atribuido', 'a_caminho')


def cancelar_entrega(encomenda):
    from ..models import Entrega
    from ..Views.notificacaoView import notificar
    # uma que já tinha falhado também termina aqui: a loja deixa de a ter por reatribuir
    entrega = (Entrega.objects.filter(encomenda=encomenda, status__in=ENTREGA_EM_CURSO + ('falhou',))
               .select_related('condutor__utilizador').first())
    if not entrega:
        return
    em_curso = entrega.status in ENTREGA_EM_CURSO
    entrega.status = 'cancelada'
    entrega.save(update_fields=['status'])
    if em_curso and entrega.condutor:
        notificar(utilizador=entrega.condutor.utilizador, tipo='entrega_cancelada',
                  titulo=f'Entrega cancelada — Encomenda #{encomenda.id}',
                  mensagem='A encomenda foi cancelada: não a entregues. Se já a levantaste, devolve-a à loja.',
                  loja=encomenda.loja, link=f'/loja/{encomenda.loja_id}/backoffice/entregas')


def fechar_entrega(encomenda):
    from django.utils import timezone
    from ..models import Entrega
    from ..Views.notificacaoView import notificar
    entrega = (Entrega.objects.filter(encomenda=encomenda, status__in=ENTREGA_EM_CURSO)
               .select_related('condutor__utilizador').first())
    if not entrega:
        return
    entrega.status = 'entregue'
    entrega.data_entrega = encomenda.data_conclusao or timezone.now()
    entrega.save(update_fields=['status', 'data_entrega'])
    if entrega.condutor:
        notificar(utilizador=entrega.condutor.utilizador, tipo='entrega_cancelada',
                  titulo=f'Entrega fechada — Encomenda #{encomenda.id}',
                  mensagem='A loja concluiu esta encomenda: já não precisas de a entregar.',
                  loja=encomenda.loja, link=f'/loja/{encomenda.loja_id}/backoffice/entregas')


def libertar_entregas(condutor, nota):
    """Saiu da equipa ou apagou a conta: ninguém ia entregar. Ficam falhadas e a loja atribui a outro."""
    from django.db import transaction
    from ..models import Entrega
    from ..Views.notificacaoView import notificar, notificar_staff
    with transaction.atomic():
        entregas = list(Entrega.objects.select_for_update(of=('self',))
                        .filter(condutor=condutor, status__in=ENTREGA_EM_CURSO)
                        .select_related('encomenda__comprador', 'encomenda__loja'))
        for entrega in entregas:
            encomenda = entrega.encomenda
            entrega.status = 'falhou'
            entrega.motivo_falha = 'outro'
            entrega.nota_falha = nota[:200]
            entrega.save(update_fields=['status', 'motivo_falha', 'nota_falha'])
            if encomenda.status == 'enviado':
                encomenda.status = 'preparando'
                encomenda.save(update_fields=['status'])
            notificar_staff(loja=encomenda.loja, roles=['dono', 'gestor'], tipo='entrega_cancelada',
                            titulo=f'Entrega sem condutor — Encomenda #{encomenda.id}',
                            mensagem=f'{nota} Atribui outro condutor.',
                            link=f'/loja/{encomenda.loja_id}/backoffice/entregas')
            notificar(utilizador=encomenda.comprador, tipo='encomenda_atualizada',
                      titulo=f'A entrega da encomenda #{encomenda.id} mudou',
                      mensagem='A loja vai atribuir outro condutor à tua encomenda.',
                      loja=encomenda.loja, link='/perfil')
    return len(entregas)


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
                        link=f'/loja/{encomenda.loja_id}/backoffice/encomendas/{encomenda.id}')


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
