"""
Devoluções e reembolsos de encomendas (o reembolso é sempre da encomenda — a Entrega é só o transporte).

Antes de receber (tipo 'cancelamento' — a encomenda é cancelada e o stock volta):
  pago (a loja ainda não começou) ou entrega falhada → o cliente cancela e é reembolsado na hora
  preparando → o cliente pede; a loja aceita ou recusa
  enviado    → não se cancela; depois de receber pede devolução
  a loja cancela uma encomenda já paga → reembolso total automático
Depois de receber (tipo 'devolucao', encomenda concluída):
  defeito / errado / em falta / não chegou → até 48h depois de concluída, em qualquer loja
  mudei de ideias → até loja.prazo_devolucao_dias (0 = a loja não aceita); o produto volta à loja,
                    o envio de volta é do cliente e a taxa de entrega não é reembolsada
  a loja aceita (pode pedir o produto de volta), recusa, ou propõe um valor mais baixo
  sem resposta da loja em 48h, recusa ou proposta rejeitada → a Bendi decide ('em_disputa')
Dinheiro (concluir): o pagamento passa a 'reembolsado'/'reembolsado_parcial'; a comissão ainda pendente
  é recalculada sobre o que fica, a já liquidada dá um CreditoComissao à loja. O reembolso no meio de
  pagamento é simulado (como os pagamentos) — ver _executar_no_gateway.

Todas as funções esperam a encomenda bloqueada (select_for_update) dentro de uma transacção.
"""
from datetime import timedelta
from decimal import Decimal

from django.core import signing
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum
from django.utils import timezone

from .dinheiro import formatar

PRAZO_PROBLEMA_H = 48           # defeito / errado / em falta / não chegou
PRAZO_RESPOSTA_LOJA_H = 48      # depois disto o pedido vai para a Bendi
PRAZO_ESCALAR_DIAS = 7          # depois de a loja recusar, o cliente pode pedir ajuda à Bendi até aqui
MAX_FOTOS = 10
MAX_TEXTO = 2000

MOTIVOS_PROBLEMA = ('defeito', 'errado', 'em_falta', 'nao_chegou')
ATIVOS = ('pedido', 'proposta', 'em_disputa', 'aguarda_produto')
NAO_CONTAM = ('recusado', 'cancelado')    # pedidos que não prendem artigos nem valor


class ErroReembolso(Exception):
    def __init__(self, mensagem, status=400):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status


def _q(v):
    return Decimal(v).quantize(Decimal('0.01'))


# ── contas da encomenda ──────────────────────────────────────────────

def pagamento_de(encomenda):
    try:
        return encomenda.pagamento
    except ObjectDoesNotExist:
        return None


def valor_pago(encomenda):
    """O que o cliente pagou de facto (o dinheiro só conta como pago quando a encomenda é concluída)."""
    p = pagamento_de(encomenda)
    if p and p.status in ('aprovado', 'reembolsado', 'reembolsado_parcial'):
        return p.valor
    return Decimal('0')


def valor_reembolsado(encomenda):
    return (encomenda.reembolsos.filter(estado='reembolsado')
            .aggregate(t=Sum('valor_aprovado'))['t'] or Decimal('0'))


def reembolsavel(encomenda):
    return max(valor_pago(encomenda) - valor_reembolsado(encomenda), Decimal('0'))


def valor_entrega(encomenda):
    produtos = sum((i.preco * i.quantidade for i in encomenda.itens.all()), Decimal('0'))
    return max(encomenda.valor_total - produtos, Decimal('0'))


def _entrega_ja_pedida(encomenda):
    return encomenda.reembolsos.exclude(estado__in=NAO_CONTAM).filter(valor_entrega__gt=0).exists()


def qtd_disponivel(encomenda):
    """{item_id: unidades que ainda se podem pedir} (descontando os pedidos em curso ou já reembolsados)."""
    from ..models import ItemReembolso
    usados = dict(ItemReembolso.objects.filter(item__encomenda=encomenda)
                  .exclude(reembolso__estado__in=NAO_CONTAM)
                  .values('item_id').annotate(q=Sum('quantidade')).values_list('item_id', 'q'))
    return {i.id: max(i.quantidade - (usados.get(i.id) or 0), 0) for i in encomenda.itens.all()}


def ativo(encomenda):
    return encomenda.reembolsos.filter(estado__in=ATIVOS).first()


def _entrega_falhou(encomenda):
    try:
        return encomenda.entrega.status == 'falhou'
    except ObjectDoesNotExist:
        return False


def _concluida_em(encomenda):
    return encomenda.data_conclusao or encomenda.data_atualizacao


def _limite(r):
    """Quanto se pode reembolsar neste pedido. Pago depois de cancelada: não há Pagamento — vale o pedido."""
    if r.motivo == 'pagamento_tardio':
        return r.valor_pedido
    return reembolsavel(r.encomenda)


# ── o que o cliente pode fazer agora ─────────────────────────────────

def modo_cancelar(encomenda):
    """'direto' (cancela já, com reembolso), 'pedido' (a loja decide) ou None."""
    if encomenda.status in ('pendente', 'pago'):
        return 'direto'
    if encomenda.status == 'preparando':
        return 'direto' if _entrega_falhou(encomenda) else 'pedido'
    return None


def opcoes(encomenda, agora=None):
    """Para a página da encomenda: o que se pode pedir agora, prazos e artigos."""
    agora = agora or timezone.now()
    em_curso = ativo(encomenda)
    res = {
        'reembolso_ativo': em_curso.id if em_curso else None,
        'cancelar': None,
        'motivos': [],
        'prazo_problema': None,
        'prazo_devolucao': None,
        'loja_aceita_devolucoes': encomenda.loja.prazo_devolucao_dias > 0,
        'reembolsavel': str(reembolsavel(encomenda)),
        'valor_entrega': str(valor_entrega(encomenda)),
        'itens': [],
    }
    if em_curso:
        return res
    res['cancelar'] = modo_cancelar(encomenda)
    if encomenda.status == 'concluido' and reembolsavel(encomenda) > 0:
        conc = _concluida_em(encomenda)
        ate_problema = conc + timedelta(hours=PRAZO_PROBLEMA_H)
        res['prazo_problema'] = ate_problema
        if agora <= ate_problema:
            res['motivos'] += list(MOTIVOS_PROBLEMA)
        dias = encomenda.loja.prazo_devolucao_dias
        if dias > 0:
            ate_devolver = conc + timedelta(days=dias)
            res['prazo_devolucao'] = ate_devolver
            if agora <= ate_devolver:
                res['motivos'].append('mudei_ideias')
        disp = qtd_disponivel(encomenda)
        res['itens'] = [{'id': i.id, 'nome': i.produto.nome if i.produto else 'Produto removido',
                         'quantidade': i.quantidade, 'disponivel': disp.get(i.id, 0), 'preco': str(i.preco),
                         'atributos': i.atributos}
                        for i in encomenda.itens.select_related('produto')]
    return res


# ── mensagens e avisos ───────────────────────────────────────────────

def mensagem(r, papel, texto, autor=None):
    from ..models import MensagemReembolso
    return MensagemReembolso.objects.create(reembolso=r, papel=papel, texto=(texto or '')[:MAX_TEXTO], autor=autor)


def _avisar_cliente(r, titulo, texto, tipo='reembolso_atualizado'):
    from ..Views.notificacaoView import notificar
    notificar(utilizador=r.comprador, tipo=tipo, titulo=f'{titulo} — Encomenda #{r.encomenda_id}',
              mensagem=texto, loja=r.loja, link=f'/perfil/reembolsos/{r.id}')


def _avisar_loja(r, titulo, texto, tipo='reembolso_atualizado'):
    from ..Views.notificacaoView import notificar_staff
    notificar_staff(loja=r.loja, roles=['dono', 'gestor'], tipo=tipo,
                    titulo=f'{titulo} — Encomenda #{r.encomenda_id}', mensagem=texto,
                    link=f'/loja/{r.loja_id}/backoffice?seccao=devolucoes&reembolso={r.id}')


def _avisar_admins(r, titulo, texto):
    from ..Views.notificacaoView import notificar_admins
    notificar_admins(tipo='reembolso_disputa', titulo=f'{titulo} — Encomenda #{r.encomenda_id}',
                     mensagem=texto, loja=r.loja, link=f'/admin?seccao=devolucoes&reembolso={r.id}')


# ── criação ──────────────────────────────────────────────────────────

def _criar(encomenda, tipo, motivo, origem, valor, entrega, descricao='', itens=None, devolver=False):
    from ..models import Reembolso, ItemReembolso
    r = Reembolso.objects.create(
        encomenda=encomenda, loja=encomenda.loja, comprador=encomenda.comprador,
        tipo=tipo, motivo=motivo, origem=origem, descricao=(descricao or '')[:MAX_TEXTO],
        valor_pedido=_q(valor), valor_entrega=_q(min(entrega, valor)), devolver_produto=devolver,
    )
    precos = {i.id: i.preco for i in encomenda.itens.all()}
    if itens is None:                                   # todos os artigos que ainda se podem pedir
        itens = {k: v for k, v in qtd_disponivel(encomenda).items() if v > 0}
    ItemReembolso.objects.bulk_create([
        ItemReembolso(reembolso=r, item_id=item_id, quantidade=q, valor=_q(precos[item_id] * q))
        for item_id, q in itens.items() if q > 0
    ])
    return r


def _cancelar_encomenda(encomenda):
    from .encomendas import repor_stock
    encomenda.status = 'cancelado'
    encomenda.save(update_fields=['status', 'data_atualizacao'])
    repor_stock(encomenda)


def cancelar_pelo_cliente(encomenda, utilizador, descricao=''):
    """
    → None (cancelada sem nada a reembolsar) ou o Reembolso (já reembolsado, ou pedido à loja).
    """
    from ..Views.notificacaoView import notificar_staff
    if ativo(encomenda):
        raise ErroReembolso('Já tens um pedido em curso para esta encomenda.')
    modo = modo_cancelar(encomenda)
    if modo is None:
        raise ErroReembolso({
            'enviado':   'A encomenda já foi enviada e não pode ser cancelada. Quando a receberes, '
                         'podes pedir a devolução.',
            'concluido': 'A encomenda já foi concluída — podes pedir uma devolução.',
            'cancelado': 'A encomenda já está cancelada.',
        }.get(encomenda.status, 'Esta encomenda não pode ser cancelada.'))

    valor = reembolsavel(encomenda)
    descricao = (descricao or '').strip()

    if modo == 'direto' and valor <= 0:
        # ainda não pagou (por pagar, ou dinheiro na entrega): cancela-se e pronto
        _cancelar_encomenda(encomenda)
        notificar_staff(loja=encomenda.loja, roles=['dono', 'gestor', 'staff'], tipo='encomenda_cancelada_loja',
                        titulo=f'Encomenda #{encomenda.id} cancelada pelo cliente',
                        mensagem='Ainda não estava paga. Stock reposto automaticamente.',
                        link=f'/loja/{encomenda.loja_id}/backoffice')
        return None

    r = _criar(encomenda, 'cancelamento', 'cancelado_cliente', 'cliente', valor, valor_entrega(encomenda),
               descricao)
    mensagem(r, 'cliente', descricao or 'Pedi o cancelamento da encomenda.', utilizador)

    if modo == 'direto':
        _cancelar_encomenda(encomenda)
        _concluir(r, valor)
        _avisar_loja(r, 'Encomenda cancelada pelo cliente',
                     f'O cliente cancelou antes da preparação e foi reembolsado em {formatar(valor)}. '
                     f'Stock reposto automaticamente.')
        return r

    r.prazo_resposta = timezone.now() + timedelta(hours=PRAZO_RESPOSTA_LOJA_H)
    r.save(update_fields=['prazo_resposta'])
    _avisar_loja(r, 'Pedido de cancelamento',
                 f'O cliente quer cancelar uma encomenda em preparação ({formatar(valor)}). '
                 f'Responde até {_hora(r.prazo_resposta)} — depois disso a Bendi decide.', 'reembolso_pedido')
    _avisar_cliente(r, 'Pedido de cancelamento enviado',
                    'A encomenda já estava em preparação, por isso a loja tem de aceitar o cancelamento.')
    return r


def pedir_devolucao(encomenda, utilizador, motivo, itens=None, descricao='', agora=None):
    """
    itens: [{'item_id', 'quantidade'}] — vazio = todos os artigos que ainda se podem pedir.
    → o Reembolso criado (estado 'pedido').
    """
    agora = agora or timezone.now()
    descricao = (descricao or '').strip()
    if encomenda.status != 'concluido':
        raise ErroReembolso('Só podes pedir uma devolução depois de receberes a encomenda.')
    if ativo(encomenda):
        raise ErroReembolso('Já tens um pedido em curso para esta encomenda.')
    if motivo not in MOTIVOS_PROBLEMA + ('mudei_ideias',):
        raise ErroReembolso('Escolhe o motivo do pedido.')
    if reembolsavel(encomenda) <= 0:
        raise ErroReembolso('Esta encomenda já foi totalmente reembolsada.')

    op = opcoes(encomenda, agora)
    if motivo not in op['motivos']:
        if motivo == 'mudei_ideias':
            raise ErroReembolso('Esta loja não aceita devoluções por mudança de ideias.'
                                if not op['loja_aceita_devolucoes']
                                else 'O prazo para devolver esta encomenda já terminou.')
        raise ErroReembolso(f'O prazo para reclamar ({PRAZO_PROBLEMA_H}h depois de receberes) já terminou.')
    if motivo in MOTIVOS_PROBLEMA and len(descricao) < 5:
        raise ErroReembolso('Descreve o problema.')

    disp = {k: v for k, v in qtd_disponivel(encomenda).items() if v > 0}
    if not disp:
        raise ErroReembolso('Já pediste o reembolso de todos os artigos desta encomenda.')
    if motivo == 'nao_chegou' or not itens:
        pedidos = dict(disp)
    else:
        pedidos = {}
        for linha in itens:
            try:
                item_id, q = int(linha.get('item_id')), int(linha.get('quantidade'))
            except (TypeError, ValueError, AttributeError):
                raise ErroReembolso('Artigos inválidos.')
            if item_id not in disp:
                raise ErroReembolso('Um dos artigos não pertence a esta encomenda ou já foi pedido.')
            if q < 1 or pedidos.get(item_id, 0) + q > disp[item_id]:
                raise ErroReembolso(f'Quantidade inválida (máximo {disp[item_id]}).')
            pedidos[item_id] = pedidos.get(item_id, 0) + q

    precos = {i.id: i.preco for i in encomenda.itens.all()}
    valor_itens = sum((precos[k] * q for k, q in pedidos.items()), Decimal('0'))
    # a taxa de entrega volta se a culpa é da loja e o pedido leva o que falta da encomenda
    tudo = all(pedidos.get(k, 0) == v for k, v in disp.items())
    entrega = (valor_entrega(encomenda) if motivo in MOTIVOS_PROBLEMA and tudo and not _entrega_ja_pedida(encomenda)
               else Decimal('0'))
    valor = min(valor_itens + entrega, reembolsavel(encomenda))

    r = _criar(encomenda, 'devolucao', motivo, 'cliente', valor, entrega, descricao, pedidos,
               devolver=(motivo == 'mudei_ideias'))
    r.prazo_resposta = agora + timedelta(hours=PRAZO_RESPOSTA_LOJA_H)
    r.save(update_fields=['prazo_resposta'])
    mensagem(r, 'cliente', descricao or 'Quero devolver.', utilizador)
    _avisar_loja(r, 'Pedido de reembolso',
                 f'{r.get_motivo_display()} · {formatar(valor)}. Responde até {_hora(r.prazo_resposta)} — '
                 f'depois disso a Bendi decide.', 'reembolso_pedido')
    _avisar_cliente(r, 'Pedido de reembolso enviado', f'A loja tem até {_hora(r.prazo_resposta)} para responder.')
    return r


def _hora(dt):
    return timezone.localtime(dt).strftime('%d/%m às %H:%M')


# ── a loja responde ──────────────────────────────────────────────────

def _resposta_loja(r, resposta):
    r.resposta_loja = resposta
    r.data_resposta_loja = timezone.now()


def _decidido(r, utilizador, admin=False):
    r.decidido_por = utilizador
    r.data_decisao = timezone.now()
    r.decisao_admin = admin


def loja_aceitar(r, utilizador, valor=None, devolver_produto=None):
    if r.estado != 'pedido':
        raise ErroReembolso('Este pedido já foi respondido.')
    enc = r.encomenda
    _decidido(r, utilizador)
    _resposta_loja(r, 'aceite')

    if r.tipo == 'cancelamento':
        if enc.status not in ('pago', 'preparando'):
            raise ErroReembolso('A encomenda já não pode ser cancelada.')
        _cancelar_encomenda(enc)
        mensagem(r, 'loja', 'A loja aceitou o cancelamento.', utilizador)
        _concluir(r, r.valor_pedido)
        return r

    if valor not in (None, ''):
        from .dinheiro import ler_valor
        valor, erro = ler_valor(valor, 'O valor')
        if erro:
            raise ErroReembolso(erro)
        if valor > r.valor_pedido:
            raise ErroReembolso(f'O valor não pode ser maior do que o pedido ({formatar(r.valor_pedido)}).')
        if valor <= 0:
            raise ErroReembolso('Para não reembolsar nada, recusa o pedido.')
    else:
        valor = r.valor_pedido

    r.devolver_produto = (r.motivo == 'mudei_ideias'
                          or (bool(devolver_produto) and r.motivo in ('defeito', 'errado')))
    r.valor_aprovado = valor
    if valor < r.valor_pedido:
        _resposta_loja(r, 'proposta')
        r.estado = 'proposta'
        r.save()
        mensagem(r, 'loja', f'A loja propõe reembolsar {formatar(valor)} (pediste {formatar(r.valor_pedido)}).',
                 utilizador)
        _avisar_cliente(r, 'A loja fez uma proposta',
                        f'Propõe reembolsar {formatar(valor)}. Aceita ou pede ajuda à Bendi.')
        return r
    if r.devolver_produto:
        r.estado = 'aguarda_produto'
        r.save()
        mensagem(r, 'loja', 'A loja aceitou. Devolve o produto à loja — o reembolso é feito quando o receber.',
                 utilizador)
        _avisar_cliente(r, 'Pedido aceite — devolve o produto',
                        'O reembolso é feito quando a loja receber o produto.'
                        + (' O envio de volta é por tua conta.' if r.motivo == 'mudei_ideias' else ''))
        return r
    r.save()
    mensagem(r, 'loja', 'A loja aceitou o pedido.', utilizador)
    _concluir(r, valor)
    return r


def loja_recusar(r, utilizador, motivo_recusa):
    motivo_recusa = (motivo_recusa or '').strip()
    if r.estado not in ('pedido', 'aguarda_produto'):
        raise ErroReembolso('Este pedido já não pode ser recusado.')
    if len(motivo_recusa) < 5:
        raise ErroReembolso('Explica ao cliente porque recusas.')
    if r.estado == 'pedido':
        _resposta_loja(r, 'recusado')
    _recusar(r, utilizador, motivo_recusa, papel='loja')
    _avisar_cliente(r, 'Pedido recusado pela loja',
                    f'Motivo: {motivo_recusa[:200]}. Se não concordas, podes pedir ajuda à Bendi '
                    f'até {PRAZO_ESCALAR_DIAS} dias.')
    return r


def _recusar(r, utilizador, motivo_recusa, papel, admin=False):
    _decidido(r, utilizador, admin)
    r.estado = 'recusado'
    r.motivo_recusa = motivo_recusa[:MAX_TEXTO]
    r.save()
    mensagem(r, papel, f'Recusado: {motivo_recusa}', utilizador)


def loja_recebido(r, utilizador, repor=False):
    """O produto devolvido chegou à loja → reembolsa (e, se está em condições, volta ao stock)."""
    from .encomendas import repor_stock
    if r.estado != 'aguarda_produto':
        raise ErroReembolso('Este pedido não está à espera do produto.')
    r.produto_recebido_em = timezone.now()
    if repor:
        repor_stock(r.encomenda, {i.item_id: i.quantidade for i in r.itens.all()})
        r.stock_reposto = True
    r.save()
    mensagem(r, 'loja', 'A loja recebeu o produto' + (' e repôs o stock.' if repor else '.'), utilizador)
    _concluir(r, r.valor_aprovado if r.valor_aprovado is not None else r.valor_pedido)
    return r


# ── o cliente responde ───────────────────────────────────────────────

def cliente_aceitar_proposta(r, utilizador):
    if r.estado != 'proposta':
        raise ErroReembolso('Não há nenhuma proposta para aceitar.')
    mensagem(r, 'cliente', f'Aceitei a proposta de {formatar(r.valor_aprovado)}.', utilizador)
    if r.devolver_produto:
        r.estado = 'aguarda_produto'
        r.save()
        _avisar_loja(r, 'Proposta aceite', 'O cliente aceitou e vai devolver o produto.')
        return r
    _concluir(r, r.valor_aprovado)
    return r


def pode_escalar(r, agora=None):
    agora = agora or timezone.now()
    if r.estado in ('proposta', 'aguarda_produto'):
        return True
    return (r.estado == 'recusado' and not r.decisao_admin and r.data_decisao is not None
            and agora <= r.data_decisao + timedelta(days=PRAZO_ESCALAR_DIAS))


def cliente_escalar(r, utilizador, texto=''):
    if not pode_escalar(r):
        raise ErroReembolso('Este pedido não pode ser enviado à Bendi.')
    if ativo(r.encomenda) not in (None, r):
        raise ErroReembolso('Já tens outro pedido em curso para esta encomenda.')
    mensagem(r, 'cliente', (texto or '').strip() or 'Pedi ajuda à Bendi.', utilizador)
    escalar(r, 'O cliente pediu ajuda à Bendi.')
    return r


def cliente_desistir(r, utilizador):
    if r.estado not in ('pedido', 'proposta', 'em_disputa', 'aguarda_produto'):
        raise ErroReembolso('Este pedido já está fechado.')
    r.estado = 'cancelado'
    r.save()
    mensagem(r, 'cliente', 'Desisti do pedido.', utilizador)
    _avisar_loja(r, 'O cliente desistiu do pedido', 'Não é preciso fazer nada.')
    return r


def escalar(r, motivo):
    r.estado = 'em_disputa'
    r.escalado_em = timezone.now()
    r.save()
    mensagem(r, 'sistema', f'{motivo} A equipa da Bendi vai analisar e decidir.')
    _avisar_admins(r, 'Reembolso para decidir', f'{r.loja.nome} · {r.get_motivo_display()} · '
                                                f'{formatar(r.valor_pedido)}. {motivo}')
    _avisar_cliente(r, 'Pedido em análise pela Bendi', 'A equipa da Bendi vai analisar e decidir.')
    _avisar_loja(r, 'Pedido em análise pela Bendi', f'{motivo} A Bendi vai decidir — podes deixar a tua versão '
                                                     f'nas mensagens do pedido.')


# ── a Bendi decide ───────────────────────────────────────────────────

def admin_decidir(r, utilizador, decisao, valor=None, devolver_produto=False, nota=''):
    nota = (nota or '').strip()
    if r.estado not in ATIVOS and not (r.estado == 'recusado' and not r.decisao_admin):
        raise ErroReembolso('Este pedido já está fechado.')
    if decisao == 'recusar':
        if len(nota) < 5:
            raise ErroReembolso('Explica a decisão.')
        _recusar(r, utilizador, nota, papel='admin', admin=True)
        _avisar_cliente(r, 'Decisão da Bendi', f'O pedido foi recusado: {nota[:200]}')
        _avisar_loja(r, 'Decisão da Bendi', 'O pedido de reembolso foi recusado.')
        return r
    if decisao != 'reembolsar':
        raise ErroReembolso('Decisão inválida.')

    limite = _limite(r)
    if valor in (None, ''):
        valor = min(r.valor_pedido, limite)
    else:
        from .dinheiro import ler_valor
        valor, erro = ler_valor(valor, 'O valor')
        if erro:
            raise ErroReembolso(erro)
    if valor <= 0:
        raise ErroReembolso('Indica um valor maior do que zero.')
    if valor > limite:
        raise ErroReembolso(f'O máximo que se pode reembolsar é {formatar(limite)}.')

    if r.estado == 'aguarda_produto':
        r.estado = 'em_disputa'          # a decisão da Bendi substitui a espera
    if ativo(r.encomenda) not in (None, r):
        raise ErroReembolso('Esta encomenda tem outro pedido em curso.')
    _decidido(r, utilizador, admin=True)
    r.valor_aprovado = valor
    mensagem(r, 'admin', f'A Bendi decidiu reembolsar {formatar(valor)}.' + (f' {nota}' if nota else ''),
             utilizador)
    enc = r.encomenda
    if r.tipo == 'cancelamento' and enc.status not in ('cancelado', 'concluido'):
        _cancelar_encomenda(enc)
    if r.tipo == 'devolucao' and devolver_produto and r.motivo in ('defeito', 'errado', 'mudei_ideias'):
        r.devolver_produto = True
        r.estado = 'aguarda_produto'
        r.save()
        _avisar_cliente(r, 'Decisão da Bendi', f'Vais receber {formatar(valor)} quando a loja receber o produto.')
        _avisar_loja(r, 'Decisão da Bendi', f'Reembolso de {formatar(valor)} quando receberes o produto.')
        return r
    r.save()
    _concluir(r, valor)
    return r


# ── automáticos ──────────────────────────────────────────────────────

def ao_cancelar_pela_loja(encomenda, utilizador=None):
    """A loja (ou o sistema) cancelou uma encomenda: se já estava paga, o cliente é reembolsado na hora."""
    em_curso = ativo(encomenda)
    if em_curso and em_curso.tipo == 'cancelamento' and em_curso.estado == 'pedido':
        _decidido(em_curso, utilizador)
        _resposta_loja(em_curso, 'aceite')
        em_curso.save()
        mensagem(em_curso, 'loja', 'A loja cancelou a encomenda.', utilizador)
        _concluir(em_curso, em_curso.valor_pedido)
        return em_curso
    valor = reembolsavel(encomenda)
    if valor <= 0:
        return None
    r = _criar(encomenda, 'cancelamento', 'cancelado_loja', 'loja' if utilizador else 'sistema',
               valor, valor_entrega(encomenda))
    _decidido(r, utilizador)
    r.save()
    mensagem(r, 'sistema', 'A loja cancelou a encomenda depois de paga — reembolso total automático.')
    _concluir(r, valor)
    return r


def ao_avancar_encomenda(encomenda, utilizador=None):
    """A loja enviou/concluiu a encomenda com um pedido de cancelamento por responder → conta como recusa."""
    em_curso = ativo(encomenda)
    if em_curso and em_curso.tipo == 'cancelamento' and em_curso.estado == 'pedido':
        txt = 'A loja enviou a encomenda.' if encomenda.status == 'enviado' else 'A loja concluiu a encomenda.'
        _resposta_loja(em_curso, 'recusado')
        _recusar(em_curso, utilizador, txt, papel='sistema')
        _avisar_cliente(em_curso, 'Cancelamento não aceite',
                        f'{txt} Se não concordas, podes pedir ajuda à Bendi.')


def pago_depois_de_cancelada(encomenda, valor, referencia):
    """
    O gateway cobrou depois de a encomenda ser cancelada (não há Pagamento): fica um pedido para a Bendi
    devolver o dinheiro (com gateway real, é a Bendi que confirma o reembolso). Um por encomenda.
    """
    from ..models import Reembolso
    if Reembolso.objects.filter(encomenda=encomenda, motivo='pagamento_tardio').exists():
        return None
    r = _criar(encomenda, 'cancelamento', 'pagamento_tardio', 'sistema', valor, Decimal('0'),
               descricao=f'Transacção cobrada: {referencia}', itens={})
    r.estado = 'em_disputa'
    r.escalado_em = timezone.now()
    r.save()
    mensagem(r, 'sistema', f'O pagamento de {formatar(valor)} chegou depois de a encomenda ser cancelada. '
                           f'A equipa da Bendi vai devolver o dinheiro.')
    _avisar_cliente(r, 'Vais ser reembolsado', f'O pagamento de {formatar(valor)} chegou depois de a encomenda '
                                               f'ser cancelada. A equipa da Bendi vai devolver-te o dinheiro.')
    return r


def escalar_sem_resposta(agora=None, lote=200):
    """Worker (a cada minuto): pedidos sem resposta da loja dentro do prazo vão para a Bendi."""
    from django.db import transaction
    from ..models import Reembolso
    agora = agora or timezone.now()
    n = 0
    with transaction.atomic():
        for r in (Reembolso.objects.select_for_update(skip_locked=True, of=('self',))
                  .filter(estado='pedido', prazo_resposta__lt=agora)
                  .select_related('loja', 'comprador').order_by('id')[:lote]):
            _resposta_loja(r, 'sem_resposta')
            escalar(r, f'A loja não respondeu em {PRAZO_RESPOSTA_LOJA_H}h.')
            n += 1
    return n


# ── dinheiro ─────────────────────────────────────────────────────────

def _executar_no_gateway(r, valor, metodo):
    """
    Devolve o dinheiro e → a referência. Os pagamentos ainda são simulados, por isso o reembolso também.
    Com gateways reais é aqui que se chama a API de reembolso (Stripe Refund / Flutterwave refunds),
    sobre a transacção do Pagamento, no valor e moeda cobrados (dinheiro.valor_cobranca).
    """
    if metodo == 'manual':
        return 'dinheiro'
    return f'simulado_{r.id}'


def _concluir(r, valor):
    from ..models import Pagamento
    enc = r.encomenda
    valor = min(_q(valor), _limite(r))
    p = pagamento_de(enc)
    metodo = ''
    if valor > 0:
        metodo = 'manual' if p and p.referencia_transacao == 'dinheiro' else 'gateway'
        r.referencia = _executar_no_gateway(r, valor, metodo)
    r.estado = 'reembolsado'
    r.valor_aprovado = valor
    r.metodo = metodo
    r.data_reembolso = timezone.now()
    r.save()

    if p and valor > 0:
        p = Pagamento.objects.select_for_update().get(pk=p.pk)
        p.status = 'reembolsado' if valor_reembolsado(enc) >= p.valor else 'reembolsado_parcial'
        p.save(update_fields=['status'])
    _ajustar_comissao(r, valor)

    if valor <= 0:
        mensagem(r, 'sistema', 'Cancelamento aceite — não havia nada pago para reembolsar.')
        _avisar_cliente(r, 'Cancelamento aceite', 'A encomenda foi cancelada. Não foi cobrado nada.')
        return r
    if metodo == 'manual':
        txt = f'Reembolso de {formatar(valor)} registado — a loja devolve o dinheiro em mão.'
    else:
        txt = f'Reembolso de {formatar(valor)} feito para o meio de pagamento usado.'
    mensagem(r, 'sistema', txt)
    _avisar_cliente(r, 'Reembolso feito', txt)
    _avisar_loja(r, 'Reembolso feito', txt)
    return r


def _ajustar_comissao(r, valor):
    """
    A plataforma devolve a comissão na proporção do reembolso: ainda pendente → recalcula-se sobre o
    que fica; já liquidada → crédito para a loja, descontado na próxima liquidação.
    """
    from ..models import Comissao, CreditoComissao
    if valor <= 0:
        return
    c = Comissao.objects.select_for_update().filter(encomenda=r.encomenda).first()
    if not c or not c.percentagem:
        return
    if c.status == 'pendente':
        antes = c.valor_comissao
        c.valor_encomenda = max(c.valor_encomenda - valor, Decimal('0'))
        c.valor_comissao = _q(c.valor_encomenda * c.percentagem / 100)
        c.notas = ((c.notas + '\n') if c.notas else '') + (
            f'Reembolso #{r.id} de {formatar(valor)}: comissão recalculada de {formatar(antes)} '
            f'para {formatar(c.valor_comissao)}.')
        c.save(update_fields=['valor_encomenda', 'valor_comissao', 'notas'])
        return
    credito = _q(valor * c.percentagem / 100)
    if credito > 0:
        CreditoComissao.objects.create(loja=r.loja, comissao=c, reembolso=r, valor=credito)


# ── papéis e fotos ───────────────────────────────────────────────────

def papel(utilizador, r):
    """'cliente' | 'loja' | 'admin' | None — quem está a ver este pedido."""
    from ..models import UtilizadorLoja
    if r.comprador_id == utilizador.id:
        return 'cliente'
    membro = UtilizadorLoja.objects.filter(loja_id=r.loja_id, utilizador=utilizador, ativo=True).first()
    if membro and membro.pode('gerir_devolucoes'):
        return 'loja'
    if utilizador.pode_admin('gerir_devolucoes'):
        return 'admin'
    return None


SALT_FOTO = 'reembolso-foto'
VALIDADE_FOTO = 60 * 60


def assinar_foto(foto_id, utilizador_id):
    return signing.dumps({'f': foto_id, 'u': utilizador_id}, salt=SALT_FOTO, compress=True)


def ler_assinatura_foto(token):
    try:
        d = signing.loads(token, salt=SALT_FOTO, max_age=VALIDADE_FOTO)
        return int(d['f']), int(d['u'])
    except (signing.BadSignature, KeyError, TypeError, ValueError):
        return None


def preparar_fotos(ficheiros, ja_tem=0):
    """Valida e converte (WebP, sem EXIF) antes de gravar → [ContentFile]. Lança ErroReembolso."""
    from ..chat import imagens
    ficheiros = list(ficheiros or [])
    if not ficheiros:
        return []
    if not imagens.imagens_disponiveis():
        raise ErroReembolso('O envio de fotos não está disponível de momento.')
    if ja_tem + len(ficheiros) > MAX_FOTOS:
        raise ErroReembolso(f'Máximo de {MAX_FOTOS} fotos por pedido.')
    prontas = []
    for f in ficheiros:
        try:
            conteudo, _, _ = imagens.processar(f)
        except imagens.ImagemInvalida as e:
            raise ErroReembolso(str(e))
        prontas.append(conteudo)
    return prontas


def gravar_fotos(r, prontas, autor, msg=None):
    from ..models import FotoReembolso
    for conteudo in prontas:
        foto = FotoReembolso(reembolso=r, mensagem=msg, autor=autor)
        foto.ficheiro.save(conteudo.name, conteudo, save=True)


# ── relatórios: vendas líquidas de reembolsos ────────────────────────

def anotar_liquido(qs):
    """
    Encomendas com `liquido` = valor_total − o que já foi reembolsado (dashboards e relatórios contam
    as vendas assim: uma encomenda concluída e depois reembolsada não é receita).
    """
    from django.db.models import DecimalField, F, OuterRef, Subquery, Value
    from django.db.models.functions import Coalesce
    from ..models import Reembolso
    reemb = (Reembolso.objects.filter(encomenda=OuterRef('pk'), estado='reembolsado')
             .values('encomenda').annotate(t=Sum('valor_aprovado')).values('t'))
    dec = DecimalField(max_digits=12, decimal_places=2)
    return qs.annotate(liquido=F('valor_total') - Coalesce(Subquery(reemb, output_field=dec), Value(Decimal('0')),
                                                           output_field=dec))


def resumo_reembolsos(qs):
    """{'total', 'count'} dos reembolsos já feitos (qs de Reembolso já filtrado por loja/período)."""
    from django.db.models import Count
    a = qs.filter(estado='reembolsado', valor_aprovado__gt=0).aggregate(t=Sum('valor_aprovado'), n=Count('id'))
    return {'total': float(a['t'] or 0), 'count': a['n'] or 0}
