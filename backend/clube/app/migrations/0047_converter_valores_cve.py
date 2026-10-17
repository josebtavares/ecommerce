"""
Passa todos os valores guardados de euros para escudos (1 EUR = 110,265 CVE).

Uma migração corre uma só vez por base de dados, por isso nunca converte duas vezes.
- Catálogo (preços de produtos, variantes, extras, entregas, POS): arredondados ao escudo.
- Planos de subscrição (e subscrições/faturas com esse valor): arredondados a 50$00.
- Histórico (encomendas, pagamentos, comissões, contas e turnos do POS, faturas avulsas):
  conversão exacta ao centavo — o mesmo valor em euros dá sempre o mesmo valor em escudos,
  por isso totais, pagamentos e comissões continuam a bater certo.
- Notificações antigas: os valores "€12.50" / "9,99 €" do texto passam para "1.378$31".
"""
import re
from decimal import Decimal, ROUND_HALF_UP

from django.db import migrations

CAMBIO = Decimal('110.265')


def exacto(v):
    return None if v is None else (Decimal(v) * CAMBIO).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def escudo(v):
    return None if v is None else (Decimal(v) * CAMBIO).quantize(Decimal('1'), rounding=ROUND_HALF_UP)


def redondo(v):
    """Preço de plano: múltiplo de 50$00 (0 fica 0)."""
    if v is None:
        return None
    return ((Decimal(v) * CAMBIO) / 50).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * 50


def formatar(v):
    inteiro, centavos = f'{abs(v):.2f}'.split('.')
    return f'{"-" if v < 0 else ""}{int(inteiro):,}'.replace(',', '.') + f'${centavos}'


def converter_campos(Modelo, campos, fn):
    for obj in Modelo.objects.all().only('pk', *campos).iterator():
        for c in campos:
            setattr(obj, c, fn(getattr(obj, c)))
        Modelo.objects.filter(pk=obj.pk).update(**{c: getattr(obj, c) for c in campos})


def converter_componentes(Modelo):
    for obj in Modelo.objects.exclude(componentes=None).only('pk', 'componentes').iterator():
        comps = obj.componentes
        if not isinstance(comps, list) or not any(isinstance(c, dict) and 'extra' in c for c in comps):
            continue
        for c in comps:
            if isinstance(c, dict) and c.get('extra') not in (None, ''):
                c['extra'] = str(exacto(c['extra']))
        Modelo.objects.filter(pk=obj.pk).update(componentes=comps)


def converter(apps, schema_editor):
    m = lambda nome, app='app': apps.get_model(app, nome)

    # catálogo
    converter_campos(m('Produto'), ['preco'], escudo)
    converter_campos(m('Inventario'), ['preco_custo', 'preco_venda'], escudo)
    converter_campos(m('VarianteProduto'), ['preco'], escudo)
    converter_campos(m('OpcaoEscolha'), ['preco_extra'], escudo)
    converter_campos(m('OpcaoEntrega'), ['preco'], escudo)
    converter_campos(m('ProdutoPOS', 'pos'), ['preco'], escudo)
    converter_campos(m('VarianteProdutoPOS', 'pos'), ['preco'], escudo)
    converter_campos(m('OpcaoEscolhaPOS', 'pos'), ['preco_extra'], escudo)

    # planos: valores redondos; subscrições e faturas com o preço de um plano ficam iguais ao plano
    precos_planos = set(m('PlanoSubscricao').objects.values_list('preco', flat=True))
    converter_campos(m('PlanoSubscricao'), ['preco'], redondo)
    de_plano = lambda v: None if v is None else (redondo(v) if v in precos_planos else exacto(v))
    converter_campos(m('Subscricao'), ['preco'], de_plano)
    converter_campos(m('FaturaSubscricao'), ['valor'], de_plano)

    # histórico
    converter_campos(m('Encomenda'), ['valor_total'], exacto)
    converter_campos(m('ItemEncomenda'), ['preco'], exacto)
    converter_campos(m('Pagamento'), ['valor'], exacto)
    converter_campos(m('Comissao'), ['valor_encomenda', 'valor_comissao'], exacto)
    converter_campos(m('ContaMesa', 'pos'),
                     ['subtotal', 'taxa_servico_valor', 'gorjeta', 'desconto_valor', 'total'], exacto)
    converter_campos(m('ItemContaMesa', 'pos'), ['preco_unitario', 'preco_total'], exacto)
    converter_campos(m('PagamentoDividido', 'pos'), ['valor'], exacto)
    converter_campos(m('TurnoPOS', 'pos'), ['valor_abertura', 'valor_fecho', 'diferenca'], exacto)
    converter_componentes(m('ItemEncomenda'))
    converter_componentes(m('ItemContaMesa', 'pos'))

    # texto das notificações antigas
    def valor_texto(txt):
        txt = txt.strip()
        if ',' in txt:                                   # "1.234,50" (pt)
            txt = txt.replace('.', '').replace(',', '.')
        try:
            return Decimal(txt)
        except Exception:
            return None

    def troca(match):
        v = valor_texto(match.group('a') or match.group('b'))
        return match.group(0) if v is None else formatar(de_plano(v))

    padrao = re.compile(r'€\s?(?P<a>-?\d+(?:[.,]\d+)*)|(?P<b>-?\d+(?:[.,]\d+)*)\s?€')
    Notificacao = m('Notificacao')
    for n in Notificacao.objects.filter(mensagem__contains='€').only('pk', 'mensagem').iterator():
        novo = padrao.sub(troca, n.mensagem)
        if novo != n.mensagem:
            Notificacao.objects.filter(pk=n.pk).update(mensagem=novo)


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0046_moeda_cve_max_digits'),
        ('pos', '0008_moeda_cve_max_digits'),
    ]

    operations = [
        migrations.RunPython(converter, migrations.RunPython.noop),
    ]
