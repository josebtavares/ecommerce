from django.db import migrations


# rascunhos — o dono da plataforma revê-os (de preferência com um jurista) em Admin → Páginas
PAGINAS = [
    {
        'slug': 'devolucoes', 'seccao': 'legal', 'ordem': 3, 'titulo': 'Devoluções e reembolsos',
        'conteudo': (
            'Cada loja da plataforma define a sua política de devolução, que aparece na página da loja e no checkout. '
            'Quando a loja não indica outra coisa, aplica-se o seguinte.\n\n'
            '## Pedir uma devolução\n'
            '- Pede a devolução no teu perfil, na encomenda, dentro do prazo indicado pela loja.\n'
            '- O produto deve ser devolvido em bom estado, com a embalagem e os acessórios.\n'
            '- Produtos perecíveis, personalizados ou de higiene pessoal podem não aceitar devolução.\n\n'
            '## Reembolsos\n'
            '- Depois de a loja aceitar a devolução, o reembolso é feito pelo mesmo meio de pagamento usado na compra.\n'
            '- Pagamentos com cartão são reembolsados no cartão; o prazo depende do banco emissor.\n'
            '- Pagamentos em dinheiro são reembolsados pela loja, que confirma a entrega do valor.\n\n'
            '## Produtos com defeito ou errados\n'
            'Se recebeste um produto com defeito ou diferente do encomendado, contacta a loja ou fala connosco através da página de contacto.'
        ),
        'dados': {},
    },
    {
        'slug': 'entregas', 'seccao': 'legal', 'ordem': 4, 'titulo': 'Entregas',
        'conteudo': (
            'As entregas são feitas por cada loja. As zonas, os custos e os prazos de cada loja aparecem no checkout antes de confirmares a encomenda.\n\n'
            '## Prazos e custos\n'
            '- O custo da entrega é mostrado no checkout e somado ao total da encomenda.\n'
            '- O prazo depende da loja, da zona e da disponibilidade dos produtos.\n\n'
            '## Levantamento na loja\n'
            'Algumas lojas permitem levantar a encomenda no local, sem custo de entrega.\n\n'
            '## Acompanhar a entrega\n'
            'Acompanhas o estado da encomenda no teu perfil. Se houver algum problema com a entrega, contacta a loja ou fala connosco através da página de contacto.'
        ),
        'dados': {},
    },
]


def migrar(apps, schema_editor):
    Pagina = apps.get_model('app', 'PaginaInstitucional')
    Config = apps.get_model('app', 'ConfiguracaoPlataforma')
    # os contactos passam da página Contacto para a configuração da plataforma (fonte única)
    cfg, _ = Config.objects.get_or_create(pk=1)
    contacto = Pagina.objects.filter(slug='contacto').first()
    dados = (contacto.dados if contacto else None) or {}
    for k in ('email', 'telefone', 'whatsapp', 'morada', 'horario'):
        campo = f'contacto_{k}'
        if not getattr(cfg, campo) and dados.get(k):
            maximo = Config._meta.get_field(campo).max_length
            setattr(cfg, campo, str(dados[k]).strip()[:maximo])
    cfg.save()
    for p in PAGINAS:
        Pagina.objects.get_or_create(slug=p['slug'], defaults=p)
    from django.core.cache import cache
    cache.delete('configuracao_plataforma')


def reverter(apps, schema_editor):
    Pagina = apps.get_model('app', 'PaginaInstitucional')
    Config = apps.get_model('app', 'ConfiguracaoPlataforma')
    cfg = Config.objects.filter(pk=1).first()
    contacto = Pagina.objects.filter(slug='contacto').first()
    if cfg and contacto:
        contacto.dados = {k: getattr(cfg, f'contacto_{k}') for k in ('email', 'telefone', 'whatsapp', 'morada', 'horario')}
        contacto.save(update_fields=['dados'])
    Pagina.objects.filter(slug__in=[p['slug'] for p in PAGINAS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0071_identificacao_legal'),
    ]

    operations = [
        migrations.RunPython(migrar, reverter),
    ]
