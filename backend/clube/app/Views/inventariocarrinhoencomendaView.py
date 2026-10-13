from django.db import transaction
from django.db.models import Q, F
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
    Loja, UtilizadorLoja, VarianteProduto,
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
from ..utils.variantes import resolver_variante, atualizar_total_inventario
from ..utils.encomendas import repor_stock
from ..utils import conjuntos as conj
from ..utils import horarios


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
        qs = (Inventario.objects
              .select_related('produto__tipo')
              .prefetch_related('produto__variantes')
              .filter(loja=loja, produto__e_conjunto=False)  # conjuntos não têm stock próprio
              .order_by('produto__nome'))

        q = request.GET.get('q')
        if q:
            qs = qs.filter(
                Q(produto__nome__icontains=q) | Q(produto__sku__icontains=q)
            )
        if request.GET.get('stock_baixo') == 'true':
            # produto simples com total baixo, ou produto com variações com ALGUMA combinação em baixo
            qs = qs.filter(
                Q(produto__stock_por_variante=False, quantidade__lte=LIMITE_STOCK_BAIXO) |
                Q(produto__stock_por_variante=True,
                  produto__variantes__ativo=True,
                  produto__variantes__quantidade__lte=LIMITE_STOCK_BAIXO)
            ).distinct()
 
        response, erro = paginar(request, qs, InventarioSerializer)
        if erro:
            return erro
        return response
 
    # POST — cria ou actualiza
    produto = get_object_or_404(Produto, id=request.data.get('produto_id'), loja=loja)
    if produto.e_conjunto:
        return Response({'detail': 'Um conjunto não tem stock próprio — o stock é o dos produtos que o compõem.'},
                        status=status.HTTP_400_BAD_REQUEST)
    if produto.stock_por_variante and 'quantidade' in request.data:
        return Response(
            {'detail': 'Este produto usa stock por variação — ajusta a quantidade de cada variação.'},
            status=status.HTTP_400_BAD_REQUEST
        )

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

def _stock_disponivel(produto, variante=None):
    """Stock da variante (se houver) ou do inventário do produto; None = sem controlo de stock."""
    if produto.e_conjunto:
        return conj.disponibilidade(produto)['quantidade']
    if variante is not None:
        return variante.quantidade
    try:
        return produto.inventario.quantidade
    except Inventario.DoesNotExist:
        return None


LIMITE_STOCK_BAIXO = 5


def _alerta_stock_baixo(loja, produto, antes, depois, variante=None):
    """Notifica dono/gestor só quando o stock CRUZA o limite (evita spam a cada venda)."""
    if not (antes > LIMITE_STOCK_BAIXO >= depois):
        return
    nome = produto.nome + (f' — {variante.descricao()}' if variante else '')
    notificar_staff(
        loja=loja,
        roles=['dono', 'gestor'],
        tipo='stock_baixo',
        titulo=f'⚠️ Stock baixo: {nome}',
        mensagem='Esgotado.' if depois <= 0 else f'Apenas {depois} unidades restantes.',
        link=f'/loja/{loja.id}/backoffice',
    )


def _msg_stock(produto, variante, disponivel):
    nome = produto.nome + (f' ({variante.descricao()})' if variante else '')
    if disponivel <= 0:
        return f'"{nome}" está esgotado.'
    return f'Stock insuficiente de "{nome}". Disponível: {disponivel}.'


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
 
    if quantidade < 1:
        return Response({'detail': 'A quantidade mínima é 1.'}, status=status.HTTP_400_BAD_REQUEST)

    carrinho, _ = Carrinho.objects.get_or_create(
        utilizador=utilizador, loja=loja
    )

    # conjunto: sem opções próprias; as escolhas do cliente (ex.: bebida) têm de ser válidas e
    # o stock é o desta combinação (fixos + escolhidos)
    escolhas = {}
    maximo_conjunto = None
    if produto.e_conjunto:
        atributos = {}
        bruto = request.data.get('escolhas') or {}
        if isinstance(bruto, str):
            import json
            try:
                bruto = json.loads(bruto)
            except (TypeError, ValueError):
                bruto = {}
        escolhas = conj.normalizar_escolhas(bruto)
        maximo_conjunto, erro_conj = conj.maximo_com_escolhas(produto, escolhas)
        if erro_conj:
            return Response({'detail': erro_conj}, status=status.HTTP_400_BAD_REQUEST)

    # produto com stock por variação → a combinação escolhida tem de existir
    variante, erro_variante = resolver_variante(produto, atributos)
    if erro_variante:
        return Response({'detail': erro_variante}, status=status.HTTP_400_BAD_REQUEST)

    # procurar item com o mesmo produto E os mesmos atributos (e as mesmas escolhas, num menu)
    item_existente = None
    for item in ItemCarrinho.objects.filter(carrinho=carrinho, produto=produto):
        if _atributos_iguais(item.atributos or {}, atributos) and (item.escolhas or {}) == escolhas:
            item_existente = item
            break

    nova_qty = quantidade + (item_existente.quantidade if item_existente else 0)
    disponivel = maximo_conjunto if produto.e_conjunto else _stock_disponivel(produto, variante)
    if disponivel is not None and nova_qty > disponivel:
        return Response(
            {'detail': _msg_stock(produto, variante, disponivel)},
            status=status.HTTP_400_BAD_REQUEST
        )

    if item_existente:
        # mesmos atributos → incrementar quantidade
        item_existente.quantidade = nova_qty
        item_existente.variante   = variante
        item_existente.save(update_fields=['quantidade', 'variante'])
    else:
        # atributos diferentes → criar item separado
        ItemCarrinho.objects.create(
            carrinho=carrinho,
            produto=produto,
            quantidade=quantidade,
            atributos=atributos,
            variante=variante,
            escolhas=escolhas,
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

    # valida stock (da variante, se o produto usar stock por variação)
    variante = item.variante
    if item.produto.stock_por_variante and not (variante and variante.ativo):
        variante, erro_variante = resolver_variante(item.produto, item.atributos)
        if erro_variante:
            return Response({'detail': erro_variante}, status=status.HTTP_400_BAD_REQUEST)
    # só valida ao AUMENTAR — reduzir tem de ser sempre possível, mesmo que o
    # stock tenha descido abaixo do que já está no carrinho
    if item.produto.e_conjunto:
        disponivel, erro_conj = conj.maximo_com_escolhas(item.produto, item.escolhas or {})
        if erro_conj and quantidade > item.quantidade:
            return Response({'detail': erro_conj}, status=status.HTTP_400_BAD_REQUEST)
    else:
        disponivel = _stock_disponivel(item.produto, variante)
    if disponivel is not None and quantidade > item.quantidade and quantidade > disponivel:
        return Response(
            {'detail': _msg_stock(item.produto, variante, disponivel)},
            status=status.HTTP_400_BAD_REQUEST
        )

    item.quantidade = quantidade
    item.variante   = variante
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
    # bloqueia a loja: se o dono/admin a fechar ao mesmo tempo, ou a encomenda é criada antes
    # (e cancelada com as outras pendentes) ou já não é criada — ver Loja.mudar_estado
    loja       = get_object_or_404(Loja.objects.select_for_update(), id=loja_id, ativa=True)
    utilizador = request.user.utilizador

    # busca o carrinho activo
    carrinho = get_object_or_404(Carrinho, utilizador=utilizador, loja=loja)

    itens = list(carrinho.itens.select_related('produto', 'variante').all())
    if not itens:
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

    # ── Agendamento escolhido pelo cliente (dia e hora dentro do horário) ──
    agendada_para, origem = None, ''
    pedido = request.data.get('agendar_para')
    if pedido:
        if not loja.agendamento_ativo:
            return Response({'detail': 'Esta loja não aceita agendamentos.', 'codigo': 'vaga_invalida'},
                            status=status.HTTP_400_BAD_REQUEST)
        agendada_para, msg = horarios.validar_vaga(loja, pedido)
        if msg:
            return Response({'detail': msg, 'codigo': 'vaga_invalida'}, status=status.HTTP_400_BAD_REQUEST)
        origem = 'cliente'

    # ── Horário: loja fechada → fica para a abertura ('agendar') ou não aceita ('bloquear') ──
    hor = horarios.estado(loja)
    if not hor['aberta']:
        if loja.fora_horario == 'bloquear' or not hor['abre_em']:
            return Response({'detail': f'A loja está fechada. Abre {horarios.quando_texto(hor["abre_em"])}.'
                                       if hor['abre_em'] else 'A loja está fechada de momento.',
                             'codigo': 'loja_fechada', 'horario': horarios.payload_publico(loja)},
                            status=status.HTTP_400_BAD_REQUEST)
        if agendada_para is None:
            # o cliente tem de ter visto o aviso — a loja pode ter fechado enquanto estava no checkout
            if request.data.get('aceita_agendamento') not in (True, 'true', '1', 1):
                return Response({'detail': f'A loja fechou entretanto. A encomenda fica para '
                                           f'{horarios.quando_texto(hor["abre_em"])} — confirma para continuar.',
                                 'codigo': 'confirmar_agendamento', 'horario': horarios.payload_publico(loja)},
                                status=status.HTTP_409_CONFLICT)
            agendada_para, origem = hor['abre_em'], 'abertura'

    # ── 1) Bloqueia e valida o stock de TODOS os itens antes de escrever ──
    # select_for_update impede que duas compras simultâneas vendam a mesma unidade.
    # O mesmo stock pode ser pedido por várias linhas (a batata sozinha e dentro de um menu):
    # soma-se tudo por linha de stock antes de comparar.
    linhas = []                       # (item, variante|None, componentes do conjunto)
    stock  = {}                       # chave → {'disp', 'pedido', 'alerta': (produto, variante)}

    def _pedir(chave, disp, qtd, alerta):
        e = stock.setdefault(chave, {'disp': disp, 'pedido': 0, 'alerta': alerta})
        ja = e['pedido']
        e['pedido'] += qtd
        return None if e['pedido'] <= e['disp'] else max(e['disp'] - ja, 0)   # sobra antes deste item

    for item in itens:
        produto  = item.produto
        variante = None
        snap     = []
        if produto.e_conjunto:
            comps, erro_conj = conj.bloquear(produto, escolhas=item.escolhas or {})
            if erro_conj:
                return Response({'detail': erro_conj}, status=status.HTTP_400_BAD_REQUEST)
            for l in comps:
                if l['chave'] is None:
                    continue
                sobra = _pedir(l['chave'], conj.stock_da_linha(l['linha']), l['por_unidade'] * item.quantidade,
                               (l['comp'].produto, l['comp'].variante))
                if sobra is not None:
                    return Response({'detail': conj.msg_sem_stock(produto, l['comp'], sobra // l['por_unidade'])},
                                    status=status.HTTP_400_BAD_REQUEST)
            snap = conj.snapshot(comps)
        else:
            if produto.stock_por_variante:
                variante, erro_variante = resolver_variante(produto, item.atributos, lock=True)
                if erro_variante:
                    return Response({'detail': erro_variante}, status=status.HTTP_400_BAD_REQUEST)
                chave, linha_stock = ('v', variante.id), variante
            else:
                inv = Inventario.objects.select_for_update().filter(produto=produto).first()
                chave, linha_stock = (('i', inv.id), inv) if inv else (None, None)
            if chave:
                sobra = _pedir(chave, linha_stock.quantidade, item.quantidade, (produto, variante))
                if sobra is not None:
                    return Response({'detail': _msg_stock(produto, variante, sobra)},
                                    status=status.HTTP_400_BAD_REQUEST)
        linhas.append((item, variante, snap))

    # calcula o total — produtos (preço da variante, se tiver) + custo de entrega
    def _preco(item, variante):
        if item.produto.e_conjunto:
            return conj.preco_com_escolhas(item.produto, item.escolhas or {})   # base + extras das escolhas
        return variante.preco if variante and variante.preco is not None else item.produto.preco

    valor_produtos = sum(_preco(item, v) * item.quantidade for item, v, _ in linhas)

    # adiciona custo da opcao de entrega se existir
    custo_entrega = 0
    opcao = None
    opcao_entrega_id = serializer.validated_data.get('opcao_entrega_id')
    if opcao_entrega_id:
        from ..models import OpcaoEntrega
        opcao = OpcaoEntrega.objects.filter(id=opcao_entrega_id, loja=loja, ativa=True).first()
        if opcao:
            custo_entrega = opcao.preco

    valor_total = valor_produtos + custo_entrega

    encomenda = Encomenda.objects.create(
        comprador      = utilizador,
        loja           = loja,
        valor_total    = valor_total,
        tipo_entrega   = serializer.validated_data.get('tipo_entrega', 'levantamento'),
        morada_entrega = serializer.validated_data.get('morada_entrega', ''),
        notas          = serializer.validated_data.get('notas', ''),
        status         = 'pendente',
        opcao_entrega  = opcao,
        agendada_para  = agendada_para,
        agendamento_origem = origem,
    )

    # ── 2) Cria os itens e desconta o stock (uma vez por linha de stock, com F()) ──
    for item, variante, snap in linhas:
        ItemEncomenda.objects.create(
            encomenda   = encomenda,
            produto     = item.produto,
            quantidade  = item.quantidade,
            preco       = _preco(item, variante),
            atributos   = item.atributos,   # ← copia os atributos
            variante    = variante,
            componentes = snap,             # conjunto: o que levava (histórico + repor stock)
        )

    for chave, e in stock.items():
        conj.descontar_chave(chave, e['pedido'])
        produto_alerta, variante_alerta = e['alerta']
        _alerta_stock_baixo(loja, produto_alerta, e['disp'], e['disp'] - e['pedido'], variante_alerta)

    notificar_staff(
        loja=loja,
        roles=['dono', 'gestor', 'staff'],
        tipo='nova_encomenda',
        titulo=f'Nova encomenda #{encomenda.id}',
        mensagem=f'Encomenda de {utilizador.nome} no valor de €{encomenda.valor_total}.'
                 + (f' Agendada pelo cliente para {horarios.texto_agendada(agendada_para)}.' if origem == 'cliente'
                    else f' Agendada para {horarios.quando_texto(agendada_para)} (feita com a loja fechada).'
                    if agendada_para else ''),
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

    # ?agendadas=1 → só as feitas com a loja fechada, ainda por preparar, da mais próxima à mais distante
    if request.GET.get('agendadas') in ('1', 'true'):
        qs = (qs.filter(agendada_para__isnull=False)
                .exclude(status__in=['enviado', 'concluido', 'cancelado'])
                .order_by('agendada_para'))

    response, erro = paginar(request, qs, EncomendaMiniSerializer)
    if erro:
        return erro
    return response


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@transaction.atomic
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
 
    # cancelado → repõe stock de todos os itens (na variante, se a compra foi de uma)
    if novo_status == 'cancelado':
        repor_stock(encomenda)
 
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
    if inventario.produto.e_conjunto:
        return Response({'detail': 'Um conjunto não tem stock próprio — o stock é o dos produtos que o compõem.'},
                        status=status.HTTP_400_BAD_REQUEST)
    if inventario.produto.stock_por_variante:
        return Response(
            {'detail': 'Este produto usa stock por variação — ajusta a quantidade de cada variação.'},
            status=status.HTTP_400_BAD_REQUEST
        )

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
