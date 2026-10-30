"""
O que acontece à volta de um pagamento online, seja qual for o fornecedor.

  iniciar_encomenda / iniciar_marcacao / iniciar_fatura → Inicio (pago já, à espera, ou ir ao fornecedor)
  confirmar(fornecedor, confirmacao)   regresso do cliente ou aviso do fornecedor → pago (ou reembolso pedido)
  reembolsar(fornecedor, transacao, valor, chave)

A nossa referência diz o que se está a pagar: enc-<id>-<método>-<ms> (encomenda), mar-… (marcação),
fat-… (fatura de subscrição). O fornecedor devolve-a e é verificada junto dele — o que o browser traz
nunca chega para dar nada como pago.
"""
import re
import time
from decimal import Decimal

from django.conf import settings
from django.db import transaction

from ..utils.banco import online_suspenso
from ..utils.dinheiro import formatar, valor_cobranca
from . import ativo, obter
from .base import Cobranca, ErroPagamento

# pagos fora da plataforma (a loja confirma quando recebe) e pagos online pelo fornecedor da plataforma.
# flutterwave/stripe/paypal são métodos antigos das lojas: passam a ser cartão pelo fornecedor activo.
METODOS_OFFLINE = ('dinheiro', 'transferencia')
METODOS_ONLINE = ('cartao', 'mobile_money', 'mbway', 'flutterwave', 'stripe', 'paypal')

_REF = re.compile(r'^(enc|mar|fat|com)-(\d{1,18})-([a-z_]{1,20})-\d{1,20}$')
_REF_ANTIGA = re.compile(r'^enc_(\d{1,18})_\d{1,20}$')       # tx_ref do Flutterwave antes desta camada
TIPOS = {'enc': 'encomenda', 'mar': 'marcacao', 'fat': 'fatura', 'com': 'comissoes'}


def nova_referencia(tipo, objeto_id, metodo):
    return f'{tipo}-{objeto_id}-{metodo}-{int(time.time() * 1000)}'


def ler_referencia(ref):
    """'enc-12-cartao-…' → ('enc', 12, 'cartao') | None."""
    ref = str(ref or '')
    m = _REF.match(ref)
    if m:
        return m.group(1), int(m.group(2)), m.group(3)
    m = _REF_ANTIGA.match(ref)
    if m:
        return 'enc', int(m.group(1)), 'flutterwave'
    return None


class DadosClienteEmFalta(ErroPagamento):
    """Pagar com cartão pede o perfil do cliente completo (contrato SISP, cl.3: nome, morada, telefone, email)."""
    codigo = 'dados_cliente'

    def __init__(self, campos):
        self.campos = campos
        nomes = {'telefone': 'o telefone', 'morada': 'a morada'}
        super().__init__(f'Para pagar com cartão, indica {" e ".join(nomes[c] for c in campos)} no teu perfil.')


def exigir_dados_cliente(utilizador, morada=''):
    """Telefone e morada (a de entrega serve) de quem paga online → DadosClienteEmFalta."""
    falta = []
    if not str(getattr(utilizador, 'telefone', '') or '').strip():
        falta.append('telefone')
    if not str(morada or getattr(utilizador, 'morada', '') or '').strip():
        falta.append('morada')
    if falta:
        raise DadosClienteEmFalta(falta)


def _regresso():
    return f'{settings.FRONTEND_BASE_URL.rstrip("/")}/pagamento/callback'


def _cliente(u):
    if not u:
        return {}
    return {'email': u.email or '', 'nome': u.nome or '', 'telefone': getattr(u, 'telefone', '') or ''}


def _bate(f, conf, valor_cve):
    """O fornecedor cobrou exactamente o que devia, na moeda certa."""
    valor, moeda = valor_cobranca(valor_cve, f.codigo)
    return conf.moeda == moeda and abs(Decimal(conf.valor) - valor) <= Decimal('0.01')


def _resultado(tipo, objeto, estado, destino):
    return {'tipo': tipo, 'id': objeto.id, 'estado': estado, 'destino': destino}


def reembolsar(fornecedor, transacao, valor, chave=''):
    """Sem fornecedor gravado (dinheiro/transferência, pagamentos de antes desta camada) → simulado."""
    return obter(fornecedor or 'simulado').reembolsar(transacao, valor, chave)


def _avisar_reembolso(titulo, mensagem, loja=None):
    """Dinheiro cobrado que não pode ficar (o que se pagava já não existe): a Bendi devolve-o. Um aviso por caso."""
    from ..models import Notificacao
    from ..Views.notificacaoView import notificar_admins
    if Notificacao.objects.filter(tipo='pagamento_reembolsar', titulo=titulo).exists():
        return
    notificar_admins(tipo='pagamento_reembolsar', titulo=titulo, mensagem=mensagem, loja=loja, link='/admin')


# ── encomendas ───────────────────────────────────────────────────────

def _limpar_carrinho(encomenda):
    from ..models import Carrinho
    carrinho = Carrinho.objects.filter(utilizador=encomenda.comprador, loja=encomenda.loja).first()
    if carrinho:
        carrinho.itens.all().delete()


def aprovar_encomenda(encomenda, metodo, transacao, fornecedor):
    """Pagamento online confirmado: Pagamento aprovado, encomenda paga, comissão registada, carrinho limpo."""
    from ..models import Comissao, Pagamento
    from ..Views.notificacaoView import notificar_admins, notificar_staff
    pagamento = Pagamento.objects.create(encomenda=encomenda, metodo=metodo, valor=encomenda.valor_total,
                                         status='aprovado', referencia_transacao=transacao, fornecedor=fornecedor)
    encomenda.status = 'pago'
    encomenda.save(update_fields=['status'])
    Comissao.registar(encomenda)
    perc = encomenda.percentagem_comissao_aplicavel     # 0 se a loja estava em subscrição
    com = (encomenda.valor_total * perc / 100).quantize(Decimal('0.01'))
    notificar_staff(
        loja=encomenda.loja, roles=['dono', 'gestor'], tipo='pagamento_aprovado',
        titulo=f'Pagamento confirmado — Encomenda #{encomenda.id}',
        mensagem=f'{formatar(encomenda.valor_total)} recebido ({obter(fornecedor).nome}). '
                 f'Receita líquida: {formatar(encomenda.valor_total - com)}.',
        link=f'/loja/{encomenda.loja_id}/backoffice',
    )
    if com:     # as lojas em subscrição não pagam comissão
        notificar_admins(
            tipo='comissao_recebida', titulo=f'Comissão registada — {encomenda.loja.nome}',
            mensagem=f'Encomenda #{encomenda.id} · Total: {formatar(encomenda.valor_total)} · '
                     f'Comissão ({perc}%): {formatar(com)}.',
            loja=encomenda.loja, link='/admin',
        )
    _limpar_carrinho(encomenda)
    return pagamento


def iniciar_encomenda(encomenda, tipo_metodo, utilizador):
    """
    A encomenda vem bloqueada e por pagar (pagamentoView._verificar_encomenda).
    Dinheiro/transferência → Pagamento pendente (a loja confirma quando recebe; a comissão fica para aí).
    Online → o fornecedor activo: aprovado logo (simulado) ou o cliente vai à página dele.
    """
    from ..models import MetodoPagamento, Pagamento
    from .base import Inicio
    if tipo_metodo not in METODOS_OFFLINE + METODOS_ONLINE:
        raise ErroPagamento('Método de pagamento inválido.')
    metodo = MetodoPagamento.objects.filter(loja=encomenda.loja, tipo=tipo_metodo, ativo=True).first()
    if not metodo:
        raise ErroPagamento('Esta loja não aceita este método de pagamento.')
    if tipo_metodo in METODOS_OFFLINE:
        Pagamento.objects.create(encomenda=encomenda, metodo=metodo, valor=encomenda.valor_total,
                                 status='pendente', referencia_transacao='dinheiro')
        encomenda.status = 'pago'           # encomenda aceite, paga-se na entrega / a loja confirma a transferência
        encomenda.save(update_fields=['status'])
        _limpar_carrinho(encomenda)
        return Inicio('pendente')
    if online_suspenso(encomenda.loja):         # sem dados bancários a Bende não sabe para onde transferir
        raise ErroPagamento('Esta loja ainda não recebe pagamentos online — escolhe outro método de pagamento.')
    exigir_dados_cliente(utilizador, encomenda.morada_entrega)
    f = ativo()
    loja = encomenda.loja
    inicio = f.iniciar(Cobranca(
        referencia=nova_referencia('enc', encomenda.id, tipo_metodo), valor=encomenda.valor_total,
        descricao=f'Encomenda #{encomenda.id}', titulo=loja.nome, logo=loja.logo.url if loja.logo else '',
        cliente=_cliente(utilizador), regresso=_regresso()))
    if inicio.estado == 'aprovado':
        aprovar_encomenda(encomenda, metodo, inicio.transacao, f.codigo)
    return inicio


@transaction.atomic
def _confirmar_encomenda(f, conf, oid, tipo_metodo):
    from ..models import Encomenda, MetodoPagamento, Pagamento
    from ..utils.devolucoes import pago_depois_de_cancelada
    enc = Encomenda.objects.select_for_update(of=('self',)).select_related('loja').filter(pk=oid).first()
    if not enc:
        raise ErroPagamento('Encomenda não encontrada.')
    destino = f'/encomenda/{enc.id}/ok'
    atual = Pagamento.objects.filter(encomenda=enc).first()
    if atual and atual.referencia_transacao == conf.transacao:
        return _resultado('encomenda', enc, 'pago', destino)          # o regresso e o aviso chegam os dois
    if not _bate(f, conf, enc.valor_total):
        raise ErroPagamento('O valor pago não corresponde à encomenda.')
    if Pagamento.objects.filter(referencia_transacao=conf.transacao).exclude(encomenda=enc).exists():
        raise ErroPagamento('Esta transacção já foi usada noutra encomenda.')
    # cobrado, mas a encomenda foi cancelada (expirou / a loja fechou) ou já estava paga → devolve-se
    if enc.status != 'pendente' or atual:
        pago_depois_de_cancelada(enc, enc.valor_total, conf.transacao)
        _avisar_reembolso(f'Reembolso necessário — Encomenda #{enc.id}',
                          f'{f.nome} confirmou {formatar(enc.valor_total)} (tx {conf.transacao}) para uma encomenda '
                          f'{"cancelada" if enc.status == "cancelado" else "já paga"} da loja {enc.loja.nome}. '
                          f'Reembolsa o cliente.', loja=enc.loja)
        return _resultado('encomenda', enc, 'reembolso', destino)
    metodo = MetodoPagamento.objects.filter(loja=enc.loja, tipo=tipo_metodo).first()
    aprovar_encomenda(enc, metodo, conf.transacao, f.codigo)
    return _resultado('encomenda', enc, 'pago', destino)


# ── marcações (pagamento antecipado) ─────────────────────────────────

def iniciar_marcacao(m, utilizador):
    """→ (Inicio, marcação). Simulado: fica paga já."""
    from ..servicos import marcacoes as ops
    ops.verificar_pagavel(m)
    if online_suspenso(m.loja):
        raise ErroPagamento('Esta loja ainda não recebe pagamentos online — a marcação não pode ser paga agora.')
    exigir_dados_cliente(utilizador)
    f = ativo()
    inicio = f.iniciar(Cobranca(
        referencia=nova_referencia('mar', m.id, 'cartao'), valor=m.preco_indicado,
        descricao=f'Marcação: {m.servico_nome}', titulo=m.loja.nome, logo=m.loja.logo.url if m.loja.logo else '',
        cliente=_cliente(utilizador), regresso=_regresso()))
    if inicio.estado == 'aprovado':
        m = ops.pagar(m, fornecedor=f.codigo, referencia=inicio.transacao)
    return inicio, m


def _confirmar_marcacao(f, conf, oid, _metodo):
    from ..utils.registo import registar
    from ..servicos import marcacoes as ops
    from ..servicos.models import Marcacao
    m = Marcacao.objects.select_related('loja').filter(pk=oid).first()
    if not m:
        raise ErroPagamento('Marcação não encontrada.')
    destino = f'/minhas-marcacoes/{m.id}'
    if m.pago and m.pagamento_referencia == conf.transacao:
        return _resultado('marcacao', m, 'pago', destino)
    if not _bate(f, conf, m.preco_indicado):
        raise ErroPagamento('O valor pago não corresponde à marcação.')
    try:
        ops.pagar(m, fornecedor=f.codigo, referencia=conf.transacao)
    except ops.ErroMarcacao as e:
        m.refresh_from_db()
        if m.pago and m.pagamento_referencia == conf.transacao:     # o aviso e o regresso chegaram ao mesmo tempo
            return _resultado('marcacao', m, 'pago', destino)
        # cobrado, mas a marcação já não pode ser paga (expirou, foi cancelada, já estava paga) → devolve-se
        registar('marcacao', 'pago_sem_efeito', objeto_id=m.id, loja_id=m.loja_id, valor=m.preco_indicado,
                           metodo=f.codigo, referencia=conf.transacao, dados={'motivo': str(e)})
        _avisar_reembolso(f'Reembolso necessário — Marcação #{m.id}',
                          f'{f.nome} confirmou {formatar(m.preco_indicado)} (tx {conf.transacao}) para uma marcação '
                          f'que já não pode ser paga ({e}). Reembolsa o cliente.', loja=m.loja)
        return _resultado('marcacao', m, 'reembolso', destino)
    return _resultado('marcacao', m, 'pago', destino)


# ── faturas de subscrição (loja ou POS) ──────────────────────────────

def _metodo_fatura(f):
    return 'simulado' if f.codigo == 'simulado' else 'online'


def iniciar_fatura(fatura, utilizador):
    from ..utils import subscricoes as subs
    if fatura.estado != 'pendente':
        raise ErroPagamento('Esta fatura já não está por pagar.')
    f = ativo()
    inicio = f.iniciar(Cobranca(
        referencia=nova_referencia('fat', fatura.id, 'cartao'), valor=fatura.valor,
        descricao=fatura.descricao[:100], titulo='Bende', cliente=_cliente(utilizador), regresso=_regresso()))
    if inicio.estado == 'aprovado':
        subs.pagar(fatura, _metodo_fatura(f), referencia=inicio.transacao)
    return inicio


def _destino_fatura(fatura):
    if fatura.pos_id:
        return '/pos/dashboard/subscricao'
    return f'/loja/{fatura.loja_id}/backoffice/subscricao'


def _confirmar_fatura(f, conf, oid, _metodo):
    from ..models import FaturaSubscricao
    from ..utils.registo import registar
    from ..utils import subscricoes as subs
    fatura = FaturaSubscricao.objects.filter(pk=oid).first()
    if not fatura:
        raise ErroPagamento('Fatura não encontrada.')
    destino = _destino_fatura(fatura)
    if fatura.estado == 'paga' and fatura.referencia == conf.transacao:
        return _resultado('fatura', fatura, 'pago', destino)
    if not _bate(f, conf, fatura.valor):
        raise ErroPagamento('O valor pago não corresponde à fatura.')
    try:
        subs.pagar(fatura, _metodo_fatura(f), referencia=conf.transacao)
    except subs.ErroFatura as e:
        fatura.refresh_from_db()
        if fatura.estado == 'paga' and fatura.referencia == conf.transacao:     # aviso e regresso ao mesmo tempo
            return _resultado('fatura', fatura, 'pago', destino)
        registar('subscricao', 'pago_sem_efeito', objeto_id=fatura.id, loja_id=fatura.loja_id,
                           pos_id=fatura.pos_id, valor=fatura.valor, metodo=f.codigo, referencia=conf.transacao,
                           dados={'motivo': str(e)})
        _avisar_reembolso(f'Reembolso necessário — Fatura #{fatura.id}',
                          f'{f.nome} confirmou {formatar(fatura.valor)} (tx {conf.transacao}) para uma fatura que '
                          f'já não está por pagar ({e}). Reembolsa o cliente.', loja=fatura.loja)
        return _resultado('fatura', fatura, 'reembolso', destino)
    return _resultado('fatura', fatura, 'pago', destino)


# ── cobrança mensal das comissões (a Bende é a comerciante: a loja paga-lhe) ──

def iniciar_cobranca_comissoes(c, utilizador):
    if c.estado != 'pendente':
        raise ErroPagamento('Esta cobrança já não está por pagar.')
    from ..utils import cobranca_comissoes as cc
    f = ativo()
    inicio = f.iniciar(Cobranca(
        referencia=nova_referencia('com', c.id, 'cartao'), valor=c.valor,
        descricao=f'Comissões até {c.mes:%m/%Y} — {c.loja.nome}'[:100], titulo='Bende', cliente=_cliente(utilizador),
        regresso=_regresso()))
    if inicio.estado == 'aprovado':
        cc.pagar(c, _metodo_fatura(f), referencia=inicio.transacao)
    return inicio


def _confirmar_cobranca(f, conf, oid, _metodo):
    from ..models import CobrancaComissoes
    from ..utils.registo import registar
    from ..utils import cobranca_comissoes as cc
    c = CobrancaComissoes.objects.select_related('loja').filter(pk=oid).first()
    if not c:
        raise ErroPagamento('Cobrança não encontrada.')
    destino = f'/loja/{c.loja_id}/backoffice/subscricao'
    if c.estado == 'paga' and c.referencia == conf.transacao:
        return _resultado('comissoes', c, 'pago', destino)
    if not _bate(f, conf, c.valor):
        raise ErroPagamento('O valor pago não corresponde à cobrança.')
    try:
        cc.pagar(c, _metodo_fatura(f), referencia=conf.transacao)
    except cc.ErroCobranca as e:
        c.refresh_from_db()
        if c.estado == 'paga' and c.referencia == conf.transacao:
            return _resultado('comissoes', c, 'pago', destino)
        registar('comissao', 'pago_sem_efeito', objeto_id=c.id, loja_id=c.loja_id, valor=c.valor, metodo=f.codigo,
                 referencia=conf.transacao, dados={'motivo': str(e)})
        _avisar_reembolso(f'Reembolso necessário — Comissões #{c.id}',
                          f'{f.nome} confirmou {formatar(c.valor)} (tx {conf.transacao}) para uma cobrança de comissões '
                          f'que já não está por pagar ({e}). Reembolsa a loja.', loja=c.loja)
        return _resultado('comissoes', c, 'reembolso', destino)
    return _resultado('comissoes', c, 'pago', destino)


# ── regresso / aviso ─────────────────────────────────────────────────

def confirmar(f, conf):
    """Confirmacao verificada no fornecedor → {tipo, id, estado: pago|reembolso, destino}. ErroPagamento se não serve."""
    lido = ler_referencia(conf.referencia)
    if not lido:
        raise ErroPagamento('Esta transacção não é de um pagamento do Bende.')
    if not conf.sucesso:
        raise ErroPagamento('Pagamento cancelado.' if conf.motivo == 'cancelado'
                            else f'O pagamento não foi confirmado ({conf.motivo or "sem resposta"}).')
    tipo, oid, metodo = lido
    return {'enc': _confirmar_encomenda, 'mar': _confirmar_marcacao, 'fat': _confirmar_fatura,
            'com': _confirmar_cobranca}[tipo](f, conf, oid, metodo)


def para_frontend(inicio, **extra):
    """Inicio → o que o frontend precisa (utils/pagamentoOnline.js segue o redirecionamento)."""
    corpo = {'estado': inicio.estado, **extra}
    if inicio.estado == 'redirecionar':
        corpo['redirecionar'] = {'url': inicio.url, 'metodo': inicio.metodo_http, 'campos': inicio.campos,
                                 'fornecedor': ativo().codigo}
    return corpo
