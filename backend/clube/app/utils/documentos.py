"""
Documentos internos em PDF (reportlab), gerados na hora — não são faturas:
- comprovativo de pagamento de uma encomenda (cliente);
- comprovativo de pagamento de uma marcação paga online (cliente) — as pagas no local não passam pela Bendi;
- comprovativo de pagamento de uma mensalidade da subscrição (dono da loja/POS);
- comprovativo de pagamento de uma cobrança mensal de comissões (dono da loja);
- extrato mensal das comissões de uma loja.
As faturas legais saem do e-Fatura e são registadas à parte (utils/fiscal.py).
"""
import io
from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from .dinheiro import formatar

RODAPE = 'Documento interno — não substitui fatura.'


def _data(d):
    if not d:
        return '—'
    if hasattr(d, 'astimezone') and getattr(d, 'tzinfo', None):
        d = timezone.localtime(d)
    return d.strftime('%d/%m/%Y')


def _hora(d):
    return timezone.localtime(d).strftime('%d/%m/%Y %H:%M') if d else '—'


def _processado_por(codigo):
    from ..pagamentos import ErroPagamento, obter
    try:
        return obter(codigo).nome
    except ErroPagamento:
        return codigo


def _cliente(p, utilizador, morada='', nif=''):
    """Nome, email, telefone e morada de quem pagou (contrato SISP, cl.3: o recibo identifica o titular)."""
    user = utilizador.user
    p.linha('Nome', user.get_full_name() or user.username)
    if nif:
        p.linha('NIF', nif)
    if user.email:
        p.linha('Email', user.email)
    if utilizador.telefone:
        p.linha('Telefone', utilizador.telefone)
    if morada or utilizador.morada:
        p.linha('Morada', (morada or utilizador.morada)[:90])


def _vendedor(p, loja, online):
    """O comerciante: com cartão é a loja (contrato vinti4 dela) — NIF e contactos sempre que os tem."""
    p.seccao('Vendedor')
    p.linha('Loja', loja.nome)
    if loja.nif and (online or loja.regime_fiscal == 'atividade'):
        p.linha('NIF', loja.nif)
    if online:
        for rotulo, v in (('Email', loja.contacto_email), ('Telefone', loja.contacto_telefone)):
            if v:
                p.linha(rotulo, v)


def _cartao_vinti4(p, prefixo, oid):
    """Recibo de um pagamento com cartão (SISP, "Validação de site do Merchant", pontos 7 e 8): comerciante,
    contactos, URL, referência única, cartão, data/hora e, com DCC, a conversão. → True se havia transacção paga."""
    from django.conf import settings
    from ..models import ConfiguracaoPlataforma, TransacaoVinti4
    tx = (TransacaoVinti4.objects.select_related('loja').filter(referencia__startswith=f'{prefixo}-{oid}-', estado='paga')
          .order_by('-terminada_em').first())
    if not tx:
        return False
    site = settings.FRONTEND_BASE_URL.rstrip('/')
    p.seccao('Comerciante')
    if tx.loja_id:                    # venda de uma loja: o comerciante é ela (contrato vinti4 dela)
        loja = tx.loja
        p.linha('Comerciante', loja.nome)
        for rotulo, v in (('Telefone', loja.contacto_telefone), ('Email', loja.contacto_email)):
            if v:
                p.linha(rotulo, v)
        p.linha('Loja virtual', f'{site}/loja/{getattr(loja, "slug", "") or loja.id}')
        cfg = ConfiguracaoPlataforma.atual()
    else:                             # comissões e subscrições: o comerciante é a Bendi
        cfg = ConfiguracaoPlataforma.atual()
        p.linha('Comerciante', f'Bendi — {cfg.titular_nome}' if cfg.titular_nome else 'Bendi')
        for rotulo, v in (('Telefone', cfg.contacto_telefone), ('Email', cfg.contacto_email)):
            if v:
                p.linha(rotulo, v)
        p.linha('Loja virtual', site)
    apoio = ' · '.join(filter(None, (cfg.contacto_email, cfg.contacto_whatsapp and f'WhatsApp {cfg.contacto_whatsapp}',
                                     cfg.contacto_horario)))
    if apoio:
        p.linha('Apoio ao cliente', apoio)
    p.seccao('Pagamento com cartão — rede vinti4')
    p.linha('Referência do pagamento', tx.ref)
    if tx.tid:
        p.linha('Nº da transação', f'{tx.periodo}-{tx.tid}')
    if tx.pan:
        p.linha('Cartão', tx.pan)
    p.linha('Data e hora', _hora(tx.terminada_em))
    p.linha('Descrição', tx.descricao or '—')
    dcc = tx.dcc or {}
    if dcc.get('dccCurrency') and dcc.get('dccAmount'):
        moeda = dcc['dccCurrency']
        p.seccao('Conversão de moeda (DCC)')
        p.linha('Taxa de conversão / Currency Conversion Rate', f'1 {moeda} = {dcc.get("dccRate", "")} CVE')
        p.linha('Taxa do serviço DCC / DCC Markup', f'{dcc.get("dccMarkup", "")} %')
        p.linha('Moeda de transação / Transaction Currency', moeda)
        p.linha('[ ] TOTAL', f'{tx.montante} CVE')
        p.linha('[x] TOTAL', f'{dcc["dccAmount"]} {moeda}', destaque=True)
        p.texto(f'I have been offered choice of currencies and agreed to pay in {moeda}.')
        p.texto('Dynamic Currency Conversion (DCC) offered by rede vinti4.')
        p.texto('Exchange rate provided by Banco de Cabo Verde.')
    return True


class _Pdf:
    """Folha A4 simples: cabeçalho, blocos de linhas rótulo/valor, tabela e rodapé."""

    def __init__(self, titulo, numero, subtitulo=''):
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        self.mm = mm
        self.buf = io.BytesIO()
        self.c = canvas.Canvas(self.buf, pagesize=A4)
        self.c.setTitle(f'{titulo} {numero}')
        self.w, self.h = A4
        self.mg = 20 * mm
        self.titulo, self.numero, self.subtitulo = titulo, numero, subtitulo
        self._cabecalho()

    def _cabecalho(self):
        c, mm = self.c, self.mm
        c.setFillColorRGB(0.86, 0.15, 0.15)
        c.rect(0, self.h - 4 * mm, self.w, 4 * mm, stroke=0, fill=1)
        c.setFillColorRGB(0.09, 0.09, 0.11)
        c.setFont('Helvetica-Bold', 22)
        c.drawString(self.mg, self.h - 24 * mm, 'Bendi')
        c.setFont('Helvetica', 9)
        c.setFillColorRGB(0.44, 0.44, 0.48)
        c.drawString(self.mg, self.h - 30 * mm, self.subtitulo)
        c.setFillColorRGB(0.09, 0.09, 0.11)
        c.setFont('Helvetica-Bold', 14)
        c.drawRightString(self.w - self.mg, self.h - 24 * mm, self.titulo)
        c.setFont('Helvetica', 9)
        c.setFillColorRGB(0.44, 0.44, 0.48)
        c.drawRightString(self.w - self.mg, self.h - 30 * mm, f'Nº {self.numero} · emitido a {_data(timezone.now())}')
        self.y = self.h - 46 * mm

    def _quebra(self, altura):
        if self.y - altura < 30 * self.mm:
            self._rodape()
            self.c.showPage()
            self._cabecalho()

    def seccao(self, titulo):
        self._quebra(12 * self.mm)
        self.c.setFont('Helvetica-Bold', 9)
        self.c.setFillColorRGB(0.44, 0.44, 0.48)
        self.c.drawString(self.mg, self.y, titulo.upper())
        self.y -= 6 * self.mm

    def linha(self, rotulo, valor, destaque=False):
        mm = self.mm
        self._quebra(9 * mm)
        c = self.c
        c.setFont('Helvetica', 9)
        c.setFillColorRGB(0.44, 0.44, 0.48)
        c.drawString(self.mg, self.y, rotulo)
        c.setFont('Helvetica-Bold' if destaque else 'Helvetica', 12 if destaque else 10)
        c.setFillColorRGB(0.09, 0.09, 0.11)
        c.drawRightString(self.w - self.mg, self.y, str(valor)[:90])
        c.setStrokeColorRGB(0.89, 0.89, 0.91)
        c.line(self.mg, self.y - 3 * mm, self.w - self.mg, self.y - 3 * mm)
        self.y -= 9 * mm

    def tabela(self, colunas, linhas):
        """colunas: [(titulo, largura_mm, 'l'|'r')]; linhas: listas de textos."""
        mm, c = self.mm, self.c

        def cabecalho():
            c.setFont('Helvetica-Bold', 8)
            c.setFillColorRGB(0.44, 0.44, 0.48)
            x = self.mg
            for titulo, larg, al in colunas:
                (c.drawRightString(x + larg * mm, self.y, titulo) if al == 'r' else c.drawString(x, self.y, titulo))
                x += larg * mm
            self.y -= 6 * mm

        self._quebra(14 * mm)
        cabecalho()
        for ln in linhas:
            if self.y - 7 * mm < 30 * mm:
                self._quebra(100 * mm)
                cabecalho()
            c.setFont('Helvetica', 9)
            c.setFillColorRGB(0.09, 0.09, 0.11)
            x = self.mg
            for (titulo, larg, al), txt in zip(colunas, ln):
                txt = str(txt)
                limite = int(larg * 0.55)            # corta textos que não cabem na coluna
                txt = txt if len(txt) <= limite else txt[:limite - 1] + '…'
                (c.drawRightString(x + larg * mm, self.y, txt) if al == 'r' else c.drawString(x, self.y, txt))
                x += larg * mm
            self.y -= 6 * mm
        self.y -= 3 * mm

    def texto(self, t, tamanho=8):
        """Uma linha de texto corrido (avisos obrigatórios do recibo)."""
        self._quebra(6 * self.mm)
        self.c.setFont('Helvetica', tamanho)
        self.c.setFillColorRGB(0.30, 0.30, 0.34)
        self.c.drawString(self.mg, self.y, str(t)[:120])
        self.y -= 5 * self.mm

    def _rodape(self, extra=''):
        c, mm = self.c, self.mm
        c.setFont('Helvetica-Bold', 8)
        c.setFillColorRGB(0.44, 0.44, 0.48)
        c.drawString(self.mg, 18 * mm, RODAPE)
        if extra:
            c.setFont('Helvetica', 8)
            c.drawString(self.mg, 13 * mm, extra[:150])

    def fim(self, extra=''):
        self._rodape(extra)
        self.c.showPage()
        self.c.save()
        return self.buf.getvalue()


# ── Encomenda ──────────────────────────────────────────────────

def nome_comprovativo_encomenda(enc):
    return f'comprovativo-encomenda-{enc.id}.pdf'


def pdf_comprovativo_encomenda(enc):
    loja = enc.loja
    pag = getattr(enc, 'pagamento', None)
    online = bool(pag and pag.fornecedor)
    p = _Pdf('Comprovativo de pagamento', f'E-{enc.id}', f'Encomenda #{enc.id} em {loja.nome}')
    _vendedor(p, loja, online)
    p.seccao('Cliente')
    _cliente(p, enc.comprador, enc.morada_entrega, enc.cliente_nif)
    p.linha('Data da encomenda', _data(enc.data_criacao))
    # checklist SISP 7.5: data de envio/entrega da mercadoria
    levantar = enc.tipo_entrega == 'levantamento'
    p.linha('Forma de entrega', enc.get_tipo_entrega_display())
    if enc.data_conclusao:
        p.linha('Levantada a' if levantar else 'Entregue a', _hora(enc.data_conclusao))
    elif enc.agendada_para:
        p.linha('Levantamento agendado para' if levantar else 'Entrega agendada para', _hora(enc.agendada_para))
    else:
        p.linha('Quando', 'Assim que a loja preparar a encomenda')

    itens = list(enc.itens.select_related('produto'))
    linhas, soma = [], 0
    for it in itens:
        sub = it.preco * it.quantidade
        soma += sub
        linhas.append([f'{it.quantidade}×', it.produto.nome if it.produto else 'Produto removido', formatar(it.preco), formatar(sub)])
    p.seccao('Artigos')
    p.tabela([('Qtd', 14, 'l'), ('Artigo', 96, 'l'), ('Preço', 30, 'r'), ('Subtotal', 30, 'r')], linhas)
    entrega = enc.valor_total - soma
    if entrega > 0:
        p.linha('Entrega', formatar(entrega))
    if enc.valor_devido != enc.valor_total:
        p.linha('Descontado (artigos esgotados)', formatar(enc.valor_devido - enc.valor_total))
    if pag:
        p.seccao('Pagamento')
        p.linha('Método de pagamento', pag.metodo.get_tipo_display() if pag.metodo_id else '—')
        p.linha('Pago a', _hora(pag.data_pagamento) if online else _data(pag.data_pagamento))
        if online:
            p.linha('Processado por', _processado_por(pag.fornecedor))
            p.linha('Referência da transação', pag.referencia_transacao[:60] or '—')
            p.linha('Estado', pag.get_status_display())
    p.linha('Total pago (CVE)', formatar(enc.valor_devido), destaque=True)
    _cartao_vinti4(p, 'enc', enc.id)
    nota = 'Pagamento simulado (ambiente de testes). ' if pag and pag.fornecedor == 'simulado' else ''
    return p.fim(nota + 'A fatura legal é emitida pela loja no e-Fatura e fica disponível na encomenda.')


# ── Marcação (serviços) ────────────────────────────────────────

def nome_comprovativo_marcacao(m):
    return f'comprovativo-marcacao-{m.id}.pdf'


def pdf_comprovativo_marcacao(m):
    """Marcação paga online (antecipado). Gerado na hora: mostra também o que já foi devolvido."""
    loja = m.loja
    online = bool(m.pagamento_fornecedor)
    p = _Pdf('Comprovativo de pagamento', f'M-{m.id}', f'Marcação #{m.id} em {loja.nome}')
    _vendedor(p, loja, online)
    p.seccao('Cliente')
    if m.cliente_id:
        _cliente(p, m.cliente)
    else:
        p.linha('Nome', m.cliente_nome or '—')
    p.seccao('Serviço')
    p.linha('Serviço', m.servico_nome)
    if m.componentes:
        p.tabela([('Inclui', 140, 'l'), ('Preço', 30, 'r')],
                 [[c.get('nome', ''), formatar(c['preco']) if c.get('preco') is not None else ''] for c in m.componentes])
    if m.profissional_id:
        p.linha('Profissional', m.profissional.nome)
    p.linha('Dia', f'{_data(m.inicio)} às {timezone.localtime(m.inicio):%H:%M}')
    p.linha('Estado', m.get_estado_display())
    p.linha('Preço', formatar(m.preco))
    p.seccao('Pagamento')
    p.linha('Pago a', _hora(m.pago_em))
    if online:
        p.linha('Processado por', _processado_por(m.pagamento_fornecedor))
        p.linha('Referência da transação', m.pagamento_referencia[:60] or '—')
    p.linha('Valor pago', formatar(m.valor_pago))
    if m.valor_reembolsado:
        p.linha('Devolvido', formatar(m.valor_reembolsado) + (f' ({_data(m.reembolsado_em)})' if m.reembolsado_em else ''))
    p.linha('Total pago', formatar(m.valor_pago - m.valor_reembolsado), destaque=True)
    _cartao_vinti4(p, 'mar', m.id)        # pago com cartão: comerciante, referência, cartão, DCC (checklist SISP 7–8)
    nota = 'Pagamento simulado (ambiente de testes). ' if m.pagamento_fornecedor == 'simulado' else ''
    return p.fim(nota + 'A fatura legal é emitida pela loja no e-Fatura e fica na marcação.')


# ── Subscrição ─────────────────────────────────────────────────

def nome_comprovativo_subscricao(f):
    return f'comprovativo-subscricao-{f.id}.pdf'


def pdf_comprovativo_subscricao(f):
    from .subscricoes import nome_alvo
    alvo = f.alvo
    p = _Pdf('Comprovativo de pagamento', f'S-{f.id}',
             'Subscrição do POS na plataforma' if f.pos_id else 'Subscrição da loja na plataforma')
    p.linha('POS' if f.pos_id else 'Loja', nome_alvo(alvo))
    if getattr(alvo, 'nif', ''):
        p.linha('NIF', alvo.nif)
    p.linha('Descrição', f.descricao)
    p.linha('Período', f'{_data(f.periodo_inicio)} a {_data(f.periodo_fim - timedelta(days=1))}')
    p.linha('Pago a', _data(f.paga_em))
    p.linha('Método', f.get_metodo_display() if f.metodo else '—')
    p.linha('Total pago', formatar(f.valor), destaque=True)
    _cartao_vinti4(p, 'fat', f.id)
    extra = 'A fatura da Bendi é emitida no e-Fatura e fica disponível na subscrição.'
    if f.metodo == 'simulado':
        extra = 'Pagamento simulado (ambiente de testes). ' + extra
    return p.fim(extra)


# ── Comissões ──────────────────────────────────────────────────

def nome_comprovativo_cobranca(c):
    return f'comprovativo-comissoes-{c.id}.pdf'


def pdf_comprovativo_cobranca(c):
    from .cobranca_comissoes import meses_da_cobranca
    loja = c.loja
    p = _Pdf('Comprovativo de pagamento', f'CC-{c.id}', 'Comissões da loja na plataforma')
    p.linha('Loja', loja.nome)
    if loja.nif:
        p.linha('NIF', loja.nif)
    p.linha('Comissões até', f'{c.mes:%m/%Y}')
    meses = meses_da_cobranca(c)
    if meses:
        p.seccao('Comissões incluídas')
        p.tabela([('Mês', 40, 'l'), ('Vendas', 30, 'r'), ('Comissões', 50, 'r'), ('Fatura da Bendi', 50, 'l')],
                 [[m['mes'][5:] + '/' + m['mes'][:4], m['comissoes'], formatar(m['total']),
                   (m['fatura'] or {}).get('numero') or 'por emitir'] for m in meses])
    p.linha('Comissões', formatar(c.valor_comissoes))
    if c.valor_creditos:
        p.linha('Créditos de reembolsos', '-' + formatar(c.valor_creditos))
    p.linha('Pago a', _data(c.paga_em))
    p.linha('Método', c.get_metodo_display() if c.metodo else '—')
    if c.referencia:
        p.linha('Referência', c.referencia)
    p.linha('Total pago', formatar(c.valor), destaque=True)
    _cartao_vinti4(p, 'com', c.id)
    extra = 'As faturas da Bendi das comissões de cada mês são emitidas no e-Fatura e chegam por email.'
    if c.metodo == 'simulado':
        extra = 'Pagamento simulado (ambiente de testes). ' + extra
    return p.fim(extra)


def comissoes_do_mes(loja, mes):
    """Comissões registadas no mês (mes = dia 1)."""
    from ..models import Comissao
    seguinte = (mes.replace(day=28) + timedelta(days=4)).replace(day=1)
    qs = (Comissao.objects.filter(loja=loja, data_criacao__date__gte=mes, data_criacao__date__lt=seguinte)
          .select_related('encomenda').order_by('data_criacao'))
    return qs, qs.aggregate(t=Sum('valor_comissao'))['t'] or 0


def creditos_do_mes(loja, mes):
    """Comissões deste mês devolvidas à loja depois de liquidadas (reembolsos) — [(crédito, comissão)], total."""
    from ..models import CreditoComissao
    qs, _ = comissoes_do_mes(loja, mes)
    cred = CreditoComissao.objects.filter(comissao__in=qs.values('id')).select_related('comissao').order_by('data_criacao')
    return cred, cred.aggregate(t=Sum('valor'))['t'] or 0


def liquido_do_mes(loja, mes):
    _, total = comissoes_do_mes(loja, mes)
    _, cred = creditos_do_mes(loja, mes)
    return total - cred


def nome_extrato_comissoes(loja, mes):
    return f'extrato-comissoes-{loja.id}-{mes:%Y-%m}.pdf'


def pdf_extrato_comissoes(loja, mes):
    qs, total = comissoes_do_mes(loja, mes)
    p = _Pdf('Extrato de comissões', f'C-{loja.id}-{mes:%Y%m}', f'{loja.nome} · {mes:%m/%Y}')
    p.linha('Loja', loja.nome)
    if loja.nif:
        p.linha('NIF', loja.nif)
    p.linha('Mês', f'{mes:%m/%Y}')
    p.seccao('Comissões')
    p.tabela([('Data', 26, 'l'), ('Encomenda', 30, 'l'), ('Valor da venda', 44, 'r'), ('%', 20, 'r'), ('Comissão', 50, 'r')],
             [[_data(c.data_criacao), f'#{c.encomenda_id}', formatar(c.valor_encomenda), f'{c.percentagem:g}%',
               formatar(c.valor_comissao)] for c in qs])
    cred, total_cred = creditos_do_mes(loja, mes)
    if total_cred:
        p.linha('Total de comissões', formatar(total))
        p.seccao('Créditos à loja (reembolsos depois de a comissão estar liquidada)')
        p.tabela([('Data', 26, 'l'), ('Encomenda', 30, 'l'), ('Crédito', 50, 'r')],
                 [[_data(c.data_criacao), f'#{c.comissao.encomenda_id}', '-' + formatar(c.valor)] for c in cred])
        p.linha('Total líquido', formatar(total - total_cred), destaque=True)
    else:
        p.linha('Total de comissões', formatar(total), destaque=True)
    return p.fim('A fatura da Bendi relativa a estas comissões é emitida no e-Fatura.')
