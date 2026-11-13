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
from . import ativo, ativo_bendi, obter
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
    """Pagar com cartão pede o perfil do cliente completo (contrato SISP, cl.3: nome, morada, telefone, email;
    o 3DS pede também a cidade — billAddrCity)."""
    codigo = 'dados_cliente'

    def __init__(self, campos):
        self.campos = campos
        nomes = {'telefone': 'o telefone', 'morada': 'a morada', 'cidade': 'o concelho ou a cidade'}
        lista = [nomes[c] for c in campos]
        texto = lista[0] if len(lista) == 1 else ', '.join(lista[:-1]) + ' e ' + lista[-1]
        super().__init__(f'Para pagar com cartão, indica {texto} no teu perfil.')


def tem_cidade(utilizador):
    """Em Cabo Verde chega o concelho; fora dele, a cidade escrita."""
    from ..utils import geografia
    if str(getattr(utilizador, 'cidade', '') or '').strip():
        return True
    return (getattr(utilizador, 'pais', 'CV') or 'CV') == 'CV' and bool(geografia.concelho(getattr(utilizador, 'concelho', '')))


def exigir_dados_cliente(utilizador, morada=''):
    """Telefone, morada (a de entrega serve) e cidade de quem paga online → DadosClienteEmFalta."""
    falta = []
    if not str(getattr(utilizador, 'telefone', '') or '').strip():
        falta.append('telefone')
    if not str(morada or getattr(utilizador, 'morada', '') or '').strip():
        falta.append('morada')
    if not tem_cidade(utilizador):
        falta.append('cidade')
    if falta:
        raise DadosClienteEmFalta(falta)


def _iniciar(f, cobranca):
    inicio = f.iniciar(cobranca)
    inicio.fornecedor = f.codigo
    return inicio


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
    notificar_admins(tipo='pagamento_reembolsar', titulo=titulo, mensagem=mensagem, loja=loja, link='/admin', email=2)


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
                 + (f'Depois da comissão da Bendi: {formatar(encomenda.valor_total - com)}. ' if com
                    else 'Sem comissão da Bendi (subscrição). ')
                 + 'A comissão da SISP pelo cartão é descontada à parte, no valor que te chega à conta. '
                   'Já podes preparar a encomenda.',
        link=f'/loja/{encomenda.loja_id}/backoffice/encomendas/{encomenda.id}',
        email=2, email_chave=f'enc:{encomenda.id}:loja_paga',      # encomenda firme: a loja tem de a preparar
    )
    if com:     # as lojas em subscrição não pagam comissão
        notificar_admins(
            tipo='comissao_recebida', titulo=f'Comissão registada — {encomenda.loja.nome}',
            mensagem=f'Encomenda #{encomenda.id} · Total: {formatar(encomenda.valor_total)} · '
                     f'Comissão ({perc}%): {formatar(com)}.',
            loja=encomenda.loja, link='/admin',
        )
    # o cliente também vê no sino que ficou paga (o email do comprovativo já segue à parte)
    from ..Views.notificacaoView import notificar
    notificar(utilizador=encomenda.comprador, tipo='encomenda_paga',
              titulo=f'Pagamento confirmado #{encomenda.id}',
              mensagem=f'{encomenda.loja.nome} recebeu o teu pagamento de {formatar(encomenda.valor_total)}. '
                       'A loja vai preparar a tua encomenda.',
              loja=encomenda.loja, link=f'/encomendas/{encomenda.id}')
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
    from ..utils import envios
    if tipo_metodo == 'dinheiro' and envios.e_envio(encomenda):
        raise ErroPagamento(envios.MSG_SEM_DINHEIRO)
    metodo = MetodoPagamento.objects.filter(loja=encomenda.loja, tipo=tipo_metodo, ativo=True).first()
    if not metodo:
        raise ErroPagamento('Esta loja não aceita este método de pagamento.')
    if tipo_metodo == 'transferencia':
        from ..utils.banco import tem_dados
        if not tem_dados(encomenda.loja):
            raise ErroPagamento('Esta loja ainda não tem os dados para transferência — escolhe outro método de pagamento.')
    if tipo_metodo in METODOS_OFFLINE:
        Pagamento.objects.create(encomenda=encomenda, metodo=metodo, valor=encomenda.valor_total,
                                 status='pendente', referencia_transacao='dinheiro')
        encomenda.status = 'pago'           # encomenda aceite, paga-se na entrega / a loja confirma a transferência
        encomenda.save(update_fields=['status'])
        _limpar_carrinho(encomenda)
        from ..Views.notificacaoView import notificar_staff
        # a encomenda ficou firme: email ao dono e gestor (o aviso no sino já foi dado ao criá-la)
        notificar_staff(loja=encomenda.loja, roles=['dono', 'gestor'], tipo='nova_encomenda', sino=False,
                        titulo=f'Nova encomenda #{encomenda.id}',
                        mensagem=f'Encomenda de {encomenda.comprador.nome} no valor de {formatar(encomenda.valor_total)}, '
                                 + ('paga por transferência — confirma-a quando o dinheiro chegar à conta.'
                                    if tipo_metodo == 'transferencia' else
                                    'paga em dinheiro na entrega.' if encomenda.tipo_entrega == 'entrega' else
                                    'paga em dinheiro no levantamento.'),
                        link=f'/loja/{encomenda.loja_id}/backoffice/encomendas/{encomenda.id}',
                        email=2, email_chave=f'enc:{encomenda.id}:loja_nova')
        if tipo_metodo == 'transferencia':  # o cliente recebe por email para onde transferir
            from ..utils.emails_fiscais import enviar_dados_transferencia
            transaction.on_commit(lambda: enviar_dados_transferencia(encomenda.pk))
            # e no sino (sem email: o dos dados para a transferência já segue) — a ficha mostra o IBAN e a referência
            from ..Views.notificacaoView import notificar
            notificar(utilizador=encomenda.comprador, tipo='encomenda_atualizada',
                      titulo=f'Encomenda recebida #{encomenda.id}',
                      mensagem=f'{encomenda.loja.nome} recebeu a tua encomenda de {formatar(encomenda.valor_total)}. '
                               'Faz a transferência com os dados da encomenda: ela segue quando a loja a confirmar.',
                      loja=encomenda.loja, link=f'/encomendas/{encomenda.id}')
        else:                               # dinheiro: confirmação da encomenda (no sino e por email)
            from ..utils import fila_emails
            from ..Views.notificacaoView import notificar
            entrega = encomenda.tipo_entrega == 'entrega'
            notificar(utilizador=encomenda.comprador, tipo='encomenda_atualizada',
                      titulo=f'Encomenda recebida #{encomenda.id}',
                      mensagem=f'{encomenda.loja.nome} recebeu a tua encomenda #{encomenda.id} de '
                               f'{formatar(encomenda.valor_total)}. Pagas em dinheiro '
                               + ('na entrega. Avisamos-te quando estiver a caminho.' if entrega
                                  else 'quando levantares na loja.'),
                      loja=encomenda.loja, link=f'/encomendas/{encomenda.id}', email=fila_emails.IMPORTANTE,
                      email_chave=f'enc:{encomenda.id}:recebida')
        return Inicio('pendente')
    if online_suspenso(encomenda.loja, utilizador):      # sem contrato vinti4 ativo (em testes: só a equipa)
        raise ErroPagamento('Esta loja ainda não recebe pagamentos online — escolhe outro método de pagamento.')
    exigir_dados_cliente(utilizador, encomenda.morada_entrega)
    f = ativo()
    loja = encomenda.loja
    inicio = _iniciar(f, Cobranca(
        referencia=nova_referencia('enc', encomenda.id, tipo_metodo), valor=encomenda.valor_total,
        descricao=f'Encomenda #{encomenda.id}', titulo=loja.nome, logo=loja.logo.url if loja.logo else '',
        cliente=_cliente(utilizador), regresso=_regresso(), pagador=utilizador, loja=loja,
        morada=encomenda.morada_entrega))
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
        cartao_loja = f.codigo == 'vinti4'          # o dinheiro foi para a conta da loja (contrato dela com a SISP)
        pago_depois_de_cancelada(enc, enc.valor_total, conf.transacao, cartao_loja=cartao_loja)
        _avisar_reembolso(f'Reembolso necessário — Encomenda #{enc.id} ({conf.transacao})',
                          f'{f.nome} confirmou {formatar(enc.valor_total)} (tx {conf.transacao}) para uma encomenda '
                          f'{"cancelada" if enc.status == "cancelado" else "já paga"} da loja {enc.loja.nome}. '
                          + ('Resolve o pedido em Devoluções: a loja faz o estorno no Portal do Comerciante da SISP.'
                             if cartao_loja else 'Reembolsa o cliente.'), loja=enc.loja)
        return _resultado('encomenda', enc, 'reembolso', destino)
    metodo = MetodoPagamento.objects.filter(loja=enc.loja, tipo=tipo_metodo).first()
    aprovar_encomenda(enc, metodo, conf.transacao, f.codigo)
    return _resultado('encomenda', enc, 'pago', destino)


# ── marcações (pagamento antecipado) ─────────────────────────────────

def iniciar_marcacao(m, utilizador):
    """→ (Inicio, marcação). Simulado: fica paga já."""
    from ..servicos import marcacoes as ops
    ops.verificar_pagavel(m)
    if online_suspenso(m.loja, utilizador):
        raise ErroPagamento('Esta loja ainda não recebe pagamentos online — a marcação não pode ser paga agora.')
    exigir_dados_cliente(utilizador)
    f = ativo()
    inicio = _iniciar(f, Cobranca(
        referencia=nova_referencia('mar', m.id, 'cartao'), valor=m.preco_indicado,
        descricao=f'Marcação: {m.servico_nome}', titulo=m.loja.nome, logo=m.loja.logo.url if m.loja.logo else '',
        cliente=_cliente(utilizador), regresso=_regresso(), pagador=utilizador, loja=m.loja))
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
    try:
        if not _bate(f, conf, m.preco_indicado):
            # o preço mudou entretanto: em escudos regista-se o que foi cobrado e devolve-se tudo
            if conf.moeda != 'CVE':
                raise ErroPagamento('O valor pago não corresponde à marcação.')
            raise ops.ErroMarcacao(f'o valor cobrado ({formatar(Decimal(conf.valor))}) não é o preço da marcação '
                                   f'({formatar(m.preco_indicado)})')
        ops.pagar(m, fornecedor=f.codigo, referencia=conf.transacao)
    except ops.ErroMarcacao as e:
        m.refresh_from_db()
        if m.pago and m.pagamento_referencia == conf.transacao:     # o aviso e o regresso chegaram ao mesmo tempo
            return _resultado('marcacao', m, 'pago', destino)
        # cobrado, mas a marcação já não pode ser paga (expirou, foi cancelada, já estava paga) → devolve-se:
        # fica na marcação como reembolso por concluir (marcacoes.pago_sem_efeito), uma vez por transacção
        from ..models import RegistoTransacao
        if RegistoTransacao.objects.filter(tipo='marcacao', evento='pago_sem_efeito', objeto_id=m.id,
                                           referencia=conf.transacao[:255]).exists():
            return _resultado('marcacao', m, 'reembolso', destino)
        # o que foi cobrado (em escudos — _bate já confirmou a moeda quando o valor bate)
        cobrado = Decimal(conf.valor) if conf.moeda == 'CVE' else m.preco_indicado
        registar('marcacao', 'pago_sem_efeito', objeto_id=m.id, loja_id=m.loja_id, valor=cobrado,
                 metodo=f.codigo, referencia=conf.transacao, dados={'motivo': str(e)})
        registado = ops.pago_sem_efeito(m, f.codigo, conf.transacao, cobrado, str(e))
        if f.codigo == 'vinti4':
            como = ('Ficou na marcação como reembolso por concluir: a loja já foi avisada para fazer o estorno no '
                    'Portal do Comerciante da SISP e marcar "Estorno feito" (Devoluções → por concluir).')
        elif registado:
            como = ('Ficou na marcação como reembolso: a devolução foi pedida ao fornecedor '
                    '(Devoluções → por concluir, se falhar).')
        else:
            como = 'Reembolsa o cliente.'
        _avisar_reembolso(f'Reembolso necessário — Marcação #{m.id} ({conf.transacao})',
                          f'{f.nome} confirmou {formatar(cobrado)} (tx {conf.transacao}) para uma marcação '
                          f'que já não pode ser paga ({e}). {como}', loja=m.loja)
        return _resultado('marcacao', m, 'reembolso', destino)
    return _resultado('marcacao', m, 'pago', destino)


# ── faturas de subscrição (loja ou POS) ──────────────────────────────

def _metodo_fatura(f):
    return 'simulado' if f.codigo == 'simulado' else 'online'


def iniciar_fatura(fatura, utilizador):
    from ..utils import subscricoes as subs
    if fatura.estado != 'pendente':
        raise ErroPagamento('Esta fatura já não está por pagar.')
    f = ativo_bendi()
    inicio = _iniciar(f, Cobranca(
        referencia=nova_referencia('fat', fatura.id, 'cartao'), valor=fatura.valor,
        descricao=fatura.descricao[:100], titulo='Bendi', cliente=_cliente(utilizador), regresso=_regresso(),
        pagador=utilizador))
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


# ── cobrança mensal das comissões (a Bendi é a comerciante: a loja paga-lhe) ──

def iniciar_cobranca_comissoes(c, utilizador):
    if c.estado != 'pendente':
        raise ErroPagamento('Esta cobrança já não está por pagar.')
    from ..utils import cobranca_comissoes as cc
    f = ativo_bendi()
    inicio = _iniciar(f, Cobranca(
        referencia=nova_referencia('com', c.id, 'cartao'), valor=c.valor,
        descricao=f'Comissões até {c.mes:%m/%Y} — {c.loja.nome}'[:100], titulo='Bendi', cliente=_cliente(utilizador),
        regresso=_regresso(), pagador=utilizador))
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
        raise ErroPagamento('Esta transacção não é de um pagamento da Bendi.')
    if not conf.sucesso:
        raise ErroPagamento('Pagamento cancelado.' if conf.motivo == 'cancelado'
                            else f'O pagamento não foi confirmado ({conf.motivo or "sem resposta"}).')
    tipo, oid, metodo = lido
    return {'enc': _confirmar_encomenda, 'mar': _confirmar_marcacao, 'fat': _confirmar_fatura,
            'com': _confirmar_cobranca}[tipo](f, conf, oid, metodo)


def destino(referencia):
    """(tipo, caminho no site) do que a referência pagava — para o regresso de um pagamento que falhou."""
    lido = ler_referencia(referencia)
    if not lido:
        return '', ''
    tipo, oid, _ = lido
    if tipo == 'enc':
        return 'encomenda', f'/encomendas/{oid}'
    if tipo == 'mar':
        return 'marcacao', f'/minhas-marcacoes/{oid}'
    if tipo == 'fat':
        from ..models import FaturaSubscricao
        fatura = FaturaSubscricao.objects.filter(pk=oid).only('pos_id', 'loja_id').first()
        return 'fatura', _destino_fatura(fatura) if fatura else ''
    from ..models import CobrancaComissoes
    loja_id = CobrancaComissoes.objects.filter(pk=oid).values_list('loja_id', flat=True).first()
    return 'comissoes', f'/loja/{loja_id}/backoffice/subscricao' if loja_id else ''


def erro_para_frontend(e):
    """ErroPagamento → corpo da resposta 400 (dados do cliente em falta: o frontend pede-os ali mesmo)."""
    extra = {'codigo': e.codigo, 'campos': e.campos} if isinstance(e, DadosClienteEmFalta) else {}
    return {'detail': str(e), **extra}


def para_frontend(inicio, **extra):
    """Inicio → o que o frontend precisa (utils/pagamentoOnline.js segue o redirecionamento)."""
    corpo = {'estado': inicio.estado, **extra}
    if inicio.estado == 'redirecionar':
        corpo['redirecionar'] = {'url': inicio.url, 'metodo': inicio.metodo_http, 'campos': inicio.campos,
                                 'fornecedor': inicio.fornecedor or ativo().codigo}
    return corpo
