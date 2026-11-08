from django.db import migrations


# Contrato SISP assinado (MD050.02, tarifário V.02): os Termos ganham a parte das lojas — comissão da Bende cobrada
# por mês, cartão só com contrato próprio da loja, comissão e prazos da SISP, débitos por reclamação/fraude (cl.4.4–4.5),
# o que a SISP proíbe (cl.4.1–4.2, 4.13). Só mexe nos Termos que ninguém editou no painel (atualizado_por vazio) e que
# ainda não têm esta secção — o texto escrito por um admin fica como está.
MARCA = '## Lojas que vendem na Bende'
ANTES_DE = '## Utilização aceitável'
SECCAO = (
    MARCA + '\n'
    '- Cada loja vende em nome próprio e responde perante o comprador pelos produtos e serviços, pelas descrições, '
    'pelos preços, pela entrega, pela fatura, pelas garantias e pelas devoluções.\n'
    '- A Bende cobra à loja uma comissão sobre as vendas concluídas, ou uma mensalidade, conforme o plano escolhido. '
    'As comissões são cobradas uma vez por mês e devem ser pagas até à data de vencimento indicada no backoffice.\n'
    '- Só pode aceitar cartões a loja que tenha o seu próprio contrato com a SISP (vinti4). O dinheiro das vendas com '
    'cartão vai diretamente para a conta da loja; a Bende não o recebe nem o guarda.\n'
    '- A SISP desconta em cada venda com cartão a comissão do seu tarifário (à data: 0,70% + IVA nos cartões vinti4 e '
    '2,5% nos cartões internacionais). Essa comissão é da SISP e não se confunde com a da Bende. O dinheiro chega no '
    'próprio dia nos cartões vinti4 e em 4 dias úteis nos internacionais.\n'
    '- Se o titular do cartão reclamar que não recebeu o produto ou o serviço, ou se a venda for considerada '
    'fraudulenta, a SISP pode debitar esse valor à loja. A loja não pode pedir ao cliente que renuncie aos seus '
    'direitos para evitar uma reclamação.\n'
    '- A loja não pode cobrar ao cliente qualquer valor extra por pagar com cartão, nem usar o cartão para cobrar '
    'dívidas, adiantar dinheiro, cobrar por conta de terceiros ou pagar com o seu próprio cartão.\n'
    '- A loja trata os dados dos clientes que recebe (nome, contactos, morada) só para cumprir as encomendas e as '
    'marcações, nos termos da lei de proteção de dados de Cabo Verde.\n\n'
)


def migrar(apps, schema_editor):
    Pagina = apps.get_model('app', 'PaginaInstitucional')
    p = Pagina.objects.filter(slug='termos', atualizado_por__isnull=True).first()
    if not p or MARCA in (p.conteudo or ''):
        return
    texto = p.conteudo or ''
    i = texto.find(ANTES_DE)
    novo = texto[:i] + SECCAO + texto[i:] if i >= 0 else texto.rstrip() + '\n\n' + SECCAO.rstrip()
    Pagina.objects.filter(pk=p.pk).update(conteudo=novo)


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0097_fila_emails'),
    ]

    operations = [
        migrations.RunPython(migrar, migrations.RunPython.noop),
    ]
