"""
Stock nas vendas do POS.

O stock pertence ao produto, não ao canal:
  - produto da loja Bendi (origem "loja") → stock da Bendi (Inventario / VarianteProduto),
    partilhado com as vendas online
  - produto próprio do POS (origem "pos")  → stock do POS (ProdutoPOS.stock / VarianteProdutoPOS)

O stock é descontado quando o item é ADICIONADO à conta (reserva enquanto está na mesa)
e reposto quando o item é removido/cancelado ou a conta é cancelada.
Chamar sempre dentro de transaction.atomic (usa select_for_update).
"""
from decimal import Decimal

from django.db.models import F

from ..models import Produto, Inventario, VarianteProduto
from ..utils.variantes import resolver_variante, atualizar_total_inventario
from .models import ProdutoPOS, VarianteProdutoPOS
from ..utils import conjuntos as conj


def _msg(nome, variante, disponivel):
    nome = nome + (f' ({variante.descricao()})' if variante else '')
    if disponivel <= 0:
        return f'"{nome}" está esgotado.'
    return f'Stock insuficiente de "{nome}". Disponível: {disponivel}.'


def reservar_stock(produto, quantidade, atributos, pos=None, escolhas=None):
    """
    Valida e desconta o stock para um item novo da conta.
    Conjunto (menu): desconta cada componente; info['componentes'] guarda o que levava.
    pos: o POS onde se vende (componentes da loja Bendi num conjunto do POS).
    produto: app.Produto ou pos.ProdutoPOS (já obtido; a linha é bloqueada aqui).
    Devolve (info, None) ou (None, mensagem_de_erro), com
      info = { variante, variante_pos, preco_unitario, nome }
    """
    e_pos = isinstance(produto, ProdutoPOS)
    modelo = ProdutoPOS if e_pos else Produto
    produto = modelo.objects.select_for_update().get(pk=produto.pk)

    info = {'variante': None, 'variante_pos': None,
            'preco_unitario': produto.preco, 'nome': produto.nome}

    if produto.e_conjunto:
        componentes, erro = conj.reservar(produto, quantidade, pos, escolhas)
        if erro:
            return None, erro
        info['componentes'] = componentes
        info['preco_unitario'] = conj.preco_com_escolhas(produto, escolhas or {})   # base + extras
        return info, None

    variante, erro = resolver_variante(produto, atributos, lock=True)
    if erro:
        return None, erro

    if variante is not None:
        if variante.quantidade < quantidade:
            return None, _msg(produto.nome, variante, variante.quantidade)
        antes = variante.quantidade
        variante.quantidade -= quantidade
        variante.save(update_fields=['quantidade', 'data_atualizacao'])
        atualizar_total_inventario(produto)
        info['variante_pos' if e_pos else 'variante'] = variante
        info['preco_unitario'] = variante.preco_efetivo
        info['nome'] = f'{produto.nome} ({variante.descricao()})'
        if not e_pos:
            _alerta(produto, antes, variante.quantidade, variante)
        return info, None

    if e_pos:
        if produto.controlar_stock:
            if produto.stock < quantidade:
                return None, _msg(produto.nome, None, produto.stock)
            produto.stock -= quantidade
            produto.save(update_fields=['stock'])
        return info, None

    inv = Inventario.objects.select_for_update().filter(produto=produto).first()
    if inv:
        if inv.quantidade < quantidade:
            return None, _msg(produto.nome, None, inv.quantidade)
        antes = inv.quantidade
        inv.quantidade -= quantidade
        inv.save(update_fields=['quantidade', 'data_atualizacao'])
        _alerta(produto, antes, inv.quantidade)
    return info, None


def custos_atuais(componentes_ou_ids):
    """{('pos'|'loja', produto_id): custo} — o preço de custo de hoje (None/0 = desconhecido não entra)."""
    pos_ids = {pid for o, pid in componentes_ou_ids if o == 'pos'}
    loja_ids = {pid for o, pid in componentes_ou_ids if o == 'loja'}
    out = {('pos', i): c for i, c in ProdutoPOS.objects.filter(id__in=pos_ids, preco_custo__isnull=False)
           .values_list('id', 'preco_custo')}
    out.update({('loja', i): c for i, c in Inventario.objects.filter(produto_id__in=loja_ids, preco_custo__gt=0)
                .values_list('produto_id', 'preco_custo')})
    return out


def custo_de_venda(produto, componentes=None):
    """
    Custo de uma unidade vendida, guardado no item (a margem dos relatórios não muda se o custo mudar depois).
    Menu: soma do custo dos componentes; se algum não tiver custo, fica sem custo (None).
    """
    origem = 'pos' if isinstance(produto, ProdutoPOS) else 'loja'
    if componentes:
        chaves = [(c.get('origem') or 'loja', c.get('produto_id')) for c in componentes]
        custos = custos_atuais(chaves)
        total = Decimal('0')
        for c, k in zip(componentes, chaves):
            custo = custos.get(k)
            if custo is None:
                return None
            total += custo * int(c.get('quantidade') or 0)
        return total
    return custos_atuais([(origem, produto.pk)]).get((origem, produto.pk))


def repor_stock_item(item):
    """Devolve ao stock as unidades de um item da conta (remoção, cancelamento)."""
    q = item.quantidade
    if item.componentes:
        # conjunto: devolve a cada componente o que se descontou (snapshot da venda)
        conj.repor(item.componentes, q)
        return
    if item.variante_pos_id:
        VarianteProdutoPOS.objects.filter(id=item.variante_pos_id).update(quantidade=F('quantidade') + q)
        atualizar_total_inventario(ProdutoPOS.objects.get(id=item.variante_pos.produto_id))
    elif item.variante_id:
        VarianteProduto.objects.filter(id=item.variante_id).update(quantidade=F('quantidade') + q)
        atualizar_total_inventario(Produto.objects.get(id=item.variante.produto_id))
    elif item.produto_pos_id:
        ProdutoPOS.objects.filter(id=item.produto_pos_id, controlar_stock=True).update(stock=F('stock') + q)
    elif item.produto_id:
        Inventario.objects.filter(produto_id=item.produto_id).update(quantidade=F('quantidade') + q)


def _alerta(produto, antes, depois, variante=None):
    # mesmo alerta de stock baixo das vendas online (dono/gestor da loja)
    from ..Views.inventariocarrinhoencomendaView import _alerta_stock_baixo
    _alerta_stock_baixo(produto.loja, produto, antes, depois, variante)


def cancelar_conta(conta, motivo='', por=''):
    """
    Cancela a conta inteira: repõe o stock dos itens não cancelados, marca-os
    cancelados, recalcula o total e liberta a mesa. Usado no POS e no admin.
    """
    conta.cancelar(motivo, por)     # repõe o stock dos itens não cancelados
    conta.items.exclude(status='cancelado').update(status='cancelado', cancelado_em=conta.cancelada_em,
                                                   cancelado_por=(por or '')[:100], atualizado_em=conta.cancelada_em)
    conta.calcular_totais()
    if conta.mesa_id:
        conta.mesa.fechar()
