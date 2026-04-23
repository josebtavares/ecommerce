from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..Views.notificacaoView import notificar_staff,notificar,notificar_admins
from decimal import Decimal


from ..models import (
    Inventario, Produto,
    Carrinho, ItemCarrinho,
    Encomenda, ItemEncomenda,
    Loja, UtilizadorLoja,
)
from ..Serializers.InventarioCarrinhoEncomendaSerializer import (
    InventarioSerializer,
    CarrinhoSerializer,
    ItemCarrinhoSerializer,
    EncomendaSerializer,
    EncomendaMiniSerializer,
    AtualizarStatusEncomendaSerializer,
)
from ..utils.pagination import paginar


# ══════════════════════════════════════════════════════════════
# HELPER
# ══════════════════════════════════════════════════════════════

def _exige_permissao(request, loja, permissao):
    try:
        membro = UtilizadorLoja.objects.get(
            loja=loja, utilizador=request.user.utilizador, ativo=True
        )
    except UtilizadorLoja.DoesNotExist:
        membro = None

    if not membro or not membro.pode(permissao):
        return None, Response(
            {'detail': f'Sem permissão: {permissao}'},
            status=status.HTTP_403_FORBIDDEN
        )
    return membro, None


# ══════════════════════════════════════════════════════════════
# INVENTÁRIO
# ══════════════════════════════════════════════════════════════



@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def inventario_list_ou_criar(request, loja_id):
    """
    GET  /app/loja/<loja_id>/inventario/  → lista inventário
    POST /app/loja/<loja_id>/inventario/  → cria ou actualiza inventário
    """
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_inventario')
    if erro:
        return erro
 
    if request.method == 'GET':
        qs = Inventario.objects.select_related('produto').filter(loja=loja)
 
        q = request.GET.get('q')
        if q:
            qs = qs.filter(
                Q(produto__nome__icontains=q) | Q(produto__sku__icontains=q)
            )
        if request.GET.get('stock_baixo') == 'true':
            qs = qs.filter(quantidade__lte=5)
 
        response, erro = paginar(request, qs, InventarioSerializer)
        if erro:
            return erro
        return response
 
    # POST — cria ou actualiza
    produto = get_object_or_404(Produto, id=request.data.get('produto_id'), loja=loja)
 
    inventario, criado = Inventario.objects.get_or_create(
        loja=loja, produto=produto,
        defaults={'quantidade': 0, 'preco_custo': 0, 'preco_venda': produto.preco}
    )
 
    serializer = InventarioSerializer(inventario, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
    serializer.save()
    return Response(
        serializer.data,
        status=status.HTTP_201_CREATED if criado else status.HTTP_200_OK
    )
# ══════════════════════════════════════════════════════════════
# CARRINHO
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def carrinho_get(request, loja_id):
    """
    GET /app/loja/<loja_id>/carrinho/
    Devolve o carrinho activo do utilizador para esta loja.
    Cria automaticamente se não existir.
    """
    loja       = get_object_or_404(Loja, id=loja_id, ativa=True)
    utilizador = request.user.utilizador

    carrinho, _ = Carrinho.objects.get_or_create(
        utilizador=utilizador, loja=loja
    )

    serializer = CarrinhoSerializer(carrinho, context={'request': request})
    return Response(serializer.data)

def _atributos_iguais(a: dict, b: dict) -> bool:
    """
    Compara dois dicts de atributos de forma normalizada.
    Ordena listas antes de comparar:
      {"cor": ["azul","vermelho"]} == {"cor": ["vermelho","azul"]} → True
    """
    if set(a.keys()) != set(b.keys()):
        return False
    for key in a:
        va = sorted(a[key]) if isinstance(a[key], list) else a[key]
        vb = sorted(b[key]) if isinstance(b[key], list) else b[key]
        if va != vb:
            return False
    return True
 
 
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def carrinho_adicionar(request, loja_id):
    """
    POST /app/loja/<loja_id>/carrinho/adicionar/
    Body: { produto_id, quantidade, atributos }
 
    Regras:
    - Mesmo produto + mesmos atributos   → incrementa quantidade
    - Mesmo produto + atributos diferentes → cria novo item separado
    """
    loja       = get_object_or_404(Loja, id=loja_id, ativa=True)
    utilizador = request.user.utilizador
 
    produto_id = request.data.get('produto_id')
    produto    = get_object_or_404(Produto, id=produto_id, loja=loja, ativo=True)
    quantidade = int(request.data.get('quantidade', 1))
    atributos  = request.data.get('atributos', {})
 
    # normalizar atributos (pode vir como string JSON do multipart)
    if isinstance(atributos, str):
        import json
        try:
            atributos = json.loads(atributos)
        except (json.JSONDecodeError, TypeError):
            atributos = {}
    if not isinstance(atributos, dict):
        atributos = {}
 
    carrinho, _ = Carrinho.objects.get_or_create(
        utilizador=utilizador, loja=loja
    )
 
    # validar stock
    try:
        stock = produto.inventario.quantidade
        if quantidade > stock:
            return Response(
                {'detail': f'Stock insuficiente. Disponível: {stock}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    except Inventario.DoesNotExist:
        pass
 
    # procurar item com o mesmo produto E os mesmos atributos
    item_existente = None
    for item in ItemCarrinho.objects.filter(carrinho=carrinho, produto=produto):
        if _atributos_iguais(item.atributos or {}, atributos):
            item_existente = item
            break
 
    if item_existente:
        # mesmos atributos → incrementar quantidade
        nova_qty = item_existente.quantidade + quantidade
        # re-validar stock com nova quantidade total
        try:
            if nova_qty > produto.inventario.quantidade:
                return Response(
                    {'detail': f'Stock insuficiente. Disponível: {produto.inventario.quantidade}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Inventario.DoesNotExist:
            pass
        item_existente.quantidade = nova_qty
        item_existente.save(update_fields=['quantidade'])
    else:
        # atributos diferentes → criar item separado
        ItemCarrinho.objects.create(
            carrinho=carrinho,
            produto=produto,
            quantidade=quantidade,
            atributos=atributos,
        )
 
    return Response(
        CarrinhoSerializer(carrinho, context={'request': request}).data,
        status=status.HTTP_200_OK
    )


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def carrinho_atualizar_item(request, loja_id, item_id):
    """
    PATCH /app/loja/<loja_id>/carrinho/item/<item_id>/
    Body: { quantidade: 3 }
    Actualiza a quantidade de um item. quantidade=0 remove o item.
    """
    utilizador = request.user.utilizador
    item       = get_object_or_404(
        ItemCarrinho,
        id=item_id,
        carrinho__utilizador=utilizador,
        carrinho__loja_id=loja_id
    )

    quantidade = int(request.data.get('quantidade', 1))

    if quantidade <= 0:
        item.delete()
        return Response({'detail': 'Item removido do carrinho.'})

    # valida stock
    try:
        stock = item.produto.inventario.quantidade
        if quantidade > stock:
            return Response(
                {'detail': f'Stock insuficiente. Disponível: {stock}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    except Inventario.DoesNotExist:
        pass

    item.quantidade = quantidade
    item.save()

    return Response(
        CarrinhoSerializer(item.carrinho, context={'request': request}).data
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def carrinho_limpar(request, loja_id):
    """DELETE /app/loja/<loja_id>/carrinho/limpar/"""
    utilizador = request.user.utilizador
    carrinho   = get_object_or_404(Carrinho, utilizador=utilizador, loja_id=loja_id)
    carrinho.itens.all().delete()
    return Response({'detail': 'Carrinho limpo.'})


# ══════════════════════════════════════════════════════════════
# ENCOMENDA
# ══════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def encomenda_criar(request, loja_id):
    """
    POST /app/loja/<loja_id>/encomenda/criar/
    Body: { tipo_entrega, morada_entrega?, notas? }
    Converte o carrinho activo numa encomenda.
    """
    loja       = get_object_or_404(Loja, id=loja_id, ativa=True)
    utilizador = request.user.utilizador

    # busca o carrinho activo
    carrinho = get_object_or_404(Carrinho, utilizador=utilizador, loja=loja)

    itens = carrinho.itens.select_related('produto__inventario').all()
    if not itens.exists():
        return Response(
            {'detail': 'O carrinho está vazio.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # valida e cria a encomenda
    serializer = EncomendaSerializer(
        data=request.data,
        context={'request': request, 'loja': loja}
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # calcula o total — produtos + custo de entrega
    valor_produtos = sum(
        item.produto.preco * item.quantidade for item in itens
    )
 
    # adiciona custo da opcao de entrega se existir
    custo_entrega = 0
    opcao_entrega_id = serializer.validated_data.get('opcao_entrega_id')
    if opcao_entrega_id:
        from ..models import OpcaoEntrega
        try:
            opcao = OpcaoEntrega.objects.get(id=opcao_entrega_id, loja=loja, ativa=True)
            custo_entrega = opcao.preco
        except OpcaoEntrega.DoesNotExist:
            pass
 
    valor_total = valor_produtos + custo_entrega
 
    encomenda = Encomenda.objects.create(
        comprador      = utilizador,
        loja           = loja,
        valor_total    = valor_total,
        tipo_entrega   = serializer.validated_data.get('tipo_entrega', 'levantamento'),
        morada_entrega = serializer.validated_data.get('morada_entrega', ''),
        notas          = serializer.validated_data.get('notas', ''),
        status         = 'pendente',
        opcao_entrega  = opcao if opcao_entrega_id else None,  # ← guarda a FK
    )

    # cria os itens da encomenda e desconta o stock
    for item in itens:
        ItemEncomenda.objects.create(
            encomenda  = encomenda,
            produto    = item.produto,
            quantidade = item.quantidade,
            preco      = item.produto.preco,
            atributos  = item.atributos,   # ← copia os atributos
        )
        # desconta stock se existir inventário
        try:
            inv = item.produto.inventario
            inv.quantidade -= item.quantidade
            inv.save(update_fields=['quantidade', 'data_atualizacao'])
        except Inventario.DoesNotExist:
            pass
        
    notificar_staff(
        loja=loja,
        roles=['dono', 'gestor', 'staff'],
        tipo='nova_encomenda',
        titulo=f'Nova encomenda #{encomenda.id}',
        mensagem=f'Encomenda de {utilizador.nome} no valor de €{encomenda.valor_total}.',
        link=f'/loja/{loja.id}/backoffice',
    )



    return Response(
        EncomendaSerializer(encomenda, context={'request': request}).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def encomenda_list_comprador(request):
    """
    GET /app/encomenda/?status=pendente&offset=0&limit=10
    Encomendas do utilizador autenticado (comprador).
    """
    utilizador = request.user.utilizador
    qs = Encomenda.objects.filter(comprador=utilizador).order_by('-data_criacao')

    s = request.GET.get('status')
    if s:
        qs = qs.filter(status=s)

    response, erro = paginar(request, qs, EncomendaMiniSerializer)
    if erro:
        return erro
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def encomenda_get(request, id):
    """
    GET /app/encomenda/<id>/
    Detalhe de uma encomenda — só o comprador ou staff da loja podem ver.
    """
    encomenda  = get_object_or_404(Encomenda, id=id)
    utilizador = request.user.utilizador

    eh_comprador = encomenda.comprador == utilizador
    eh_staff     = UtilizadorLoja.objects.filter(
        loja=encomenda.loja, utilizador=utilizador, ativo=True
    ).exists()

    if not eh_comprador and not eh_staff:
        return Response({'detail': 'Sem permissão.'}, status=status.HTTP_403_FORBIDDEN)

    serializer = EncomendaSerializer(encomenda, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def encomenda_list_loja(request, loja_id):
    """
    GET /app/loja/<loja_id>/encomendas/?status=pendente&offset=0&limit=20
    Backoffice — lista encomendas da loja.
    """
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_encomendas')
    if erro:
        return erro

    qs = Encomenda.objects.filter(loja=loja).order_by('-data_criacao')

    s = request.GET.get('status')
    if s:
        qs = qs.filter(status=s)

    response, erro = paginar(request, qs, EncomendaMiniSerializer)
    if erro:
        return erro
    return response


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def encomenda_atualizar_status(request, loja_id, id):
    """
    PATCH /app/loja/<loja_id>/encomendas/<id>/status/
    Body: { status: 'preparando' }
    - cancelado  → repõe stock
    - concluido + dinheiro → aprova pagamento + regista comissao
    """
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_encomendas')
    if erro:
        return erro
 
    encomenda  = get_object_or_404(Encomenda, id=id, loja=loja)
    serializer = AtualizarStatusEncomendaSerializer(
        encomenda, data=request.data, partial=True
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
    novo_status = serializer.validated_data.get('status')
    serializer.save()
 
    # cancelado → repõe stock de todos os itens
    if novo_status == 'cancelado':
        for item in encomenda.itens.select_related('produto__inventario').all():
            try:
                inv = item.produto.inventario
                inv.quantidade += item.quantidade
                inv.save(update_fields=['quantidade', 'data_atualizacao'])
            except Exception:
                pass
 
    # concluido + dinheiro → aprova pagamento e regista comissao
    if novo_status == 'concluido':
        try:
            pagamento = encomenda.pagamento
            if pagamento.referencia_transacao == 'dinheiro' and pagamento.status == 'pendente':
                from django.utils.timezone import now
                pagamento.status = 'aprovado'
                pagamento.save(update_fields=['status'])
                from ..models import Comissao
                Comissao.registar(encomenda)
        except Exception:
            pass
    MSGS_COMPRADOR = {
        'pago':       ('Encomenda confirmada',   'O pagamento foi confirmado. A loja está a preparar o teu pedido.', 'encomenda_paga'),
        'preparando': ('Encomenda em preparação','A tua encomenda está a ser preparada.',                            'encomenda_atualizada'),
        'enviado':    ('Encomenda enviada',       'A tua encomenda está a caminho!',                                 'encomenda_enviada'),
        'concluido':  ('Encomenda concluída',     'A tua encomenda foi entregue. Obrigado pela compra!',             'encomenda_concluida'),
        'cancelado':  ('Encomenda cancelada',     f'A tua encomenda #{encomenda.id} foi cancelada.',                 'encomenda_cancelada'),
    }
    if novo_status in MSGS_COMPRADOR:
        titulo, msg, tipo_c = MSGS_COMPRADOR[novo_status]
        notificar(
            utilizador=encomenda.comprador,
            tipo=tipo_c,
            titulo=f'{titulo} #{encomenda.id}',
            mensagem=msg,
            loja=encomenda.loja,
            link='/perfil',
        )
 
    # ── Notifica dono/gestor quando concluído ─────────────────
    if novo_status == 'concluido':
        _perc = encomenda.loja.percentagem_comissao
        _com  = (encomenda.valor_total * _perc / 100).quantize(Decimal('0.01'))
        _liq  = encomenda.valor_total - _com
 
        notificar_staff(
            loja=encomenda.loja,
            roles=['dono', 'gestor'],
            tipo='encomenda_concluida_loja',
            titulo=f'Encomenda #{encomenda.id} concluída ✓',
            mensagem=f'Receita: €{encomenda.valor_total} · Comissão ({_perc}%): €{_com} · Líquido: €{_liq}.',
            link=f'/loja/{encomenda.loja_id}/backoffice',
        )
 
        # notifica admins se pagamento era dinheiro (comissão registada agora)
        try:
            if encomenda.pagamento.referencia_transacao == 'dinheiro':
                notificar_admins(
                    tipo='comissao_recebida',
                    titulo=f'Comissão registada (dinheiro) — {encomenda.loja.nome}',
                    mensagem=f'Encomenda #{encomenda.id} concluída · Comissão: €{_com}.',
                    loja=encomenda.loja,
                    link='/admin',
                )
        except Exception:
            pass
 
    # ── Notifica loja quando cancelado ───────────────────────
    if novo_status == 'cancelado':
        notificar_staff(
            loja=encomenda.loja,
            roles=['dono', 'gestor', 'staff'],
            tipo='encomenda_cancelada_loja',
            titulo=f'Encomenda #{encomenda.id} cancelada',
            mensagem='Stock reposto automaticamente.',
            link=f'/loja/{encomenda.loja_id}/backoffice',
        )
 
    return Response(
        EncomendaSerializer(encomenda, context={'request': request}).data
    )
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def carrinho_list_utilizador(request):
    """
    GET /app/carrinho/
    Devolve todos os carrinhos activos do utilizador autenticado.
    Só inclui carrinhos com itens.
    """
    utilizador = request.user.utilizador
    carrinhos = Carrinho.objects.filter(
        utilizador=utilizador
    ).prefetch_related('itens__produto__inventario').all()

    # só devolve carrinhos com itens
    carrinhos = [c for c in carrinhos if c.itens.exists()]

    serializer = CarrinhoSerializer(carrinhos, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def inventario_ajustar_stock(request, loja_id, produto_id):
    loja = get_object_or_404(Loja, id=loja_id)
    _, erro = _exige_permissao(request, loja, 'gerir_inventario')
    if erro:
        return erro

    inventario = get_object_or_404(Inventario, loja=loja, produto_id=produto_id)

    try:
        ajuste = int(request.data.get('ajuste', 0))
    except ValueError:
        return Response({'detail': 'ajuste deve ser um número inteiro.'}, status=400)

    nova_qty = inventario.quantidade + ajuste
    if nova_qty < 0:
        return Response(
            {'detail': f'Stock insuficiente. Actual: {inventario.quantidade}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    inventario.quantidade = nova_qty
    inventario.save(update_fields=['quantidade', 'data_atualizacao'])
    if inventario.quantidade <= 5:
        notificar_staff(
            loja=loja,
            roles=['dono', 'gestor'],
            tipo='stock_baixo',
            titulo=f'⚠️ Stock baixo: {inventario.produto.nome}',
            mensagem=f'Apenas {inventario.quantidade} unidades restantes.',
            link=f'/loja/{loja.id}/backoffice',
        )
    return Response(InventarioSerializer(inventario).data)