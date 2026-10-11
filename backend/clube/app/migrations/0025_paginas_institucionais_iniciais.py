from django.db import migrations


PAGINAS = [
    {
        'slug': 'ajuda', 'seccao': 'suporte', 'ordem': 1, 'titulo': 'Ajuda',
        'conteudo': (
            'Bem-vindo ao centro de ajuda. Aqui encontras o essencial para comprar e vender na plataforma.\n\n'
            '## Comprar\n'
            '- Explora as lojas e adiciona produtos ao carrinho.\n'
            '- Cada loja tem o seu carrinho e as suas opções de entrega e pagamento.\n'
            '- Acompanha as tuas encomendas no teu perfil.\n\n'
            '## Vender\n'
            '- Cria a tua loja a partir do teu perfil.\n'
            '- Gere produtos, stock, encomendas e entregas no backoffice da loja.\n\n'
            'Não encontraste o que procuravas? Consulta as perguntas frequentes ou fala connosco através da página de contacto.'
        ),
        'dados': {},
    },
    {
        'slug': 'contacto', 'seccao': 'suporte', 'ordem': 2, 'titulo': 'Contacto',
        'conteudo': 'Estamos disponíveis para ajudar. Escolhe a forma de contacto que te for mais conveniente.',
        'dados': {'email': '', 'telefone': '', 'whatsapp': '', 'morada': '', 'horario': 'Segunda a sexta, 9h–18h'},
    },
    {
        'slug': 'faq', 'seccao': 'suporte', 'ordem': 3, 'titulo': 'Perguntas frequentes',
        'conteudo': '',
        'dados': {'perguntas': [
            {'pergunta': 'Como faço uma encomenda?',
             'resposta': 'Abre a loja, escolhe os produtos, adiciona-os ao carrinho e finaliza a compra no checkout.'},
            {'pergunta': 'Que métodos de pagamento posso usar?',
             'resposta': 'Depende de cada loja. Os métodos aceites aparecem na página da loja e no checkout.'},
            {'pergunta': 'Como acompanho a minha encomenda?',
             'resposta': 'No teu perfil, na secção de encomendas, vês o estado de cada encomenda em tempo real.'},
            {'pergunta': 'Como crio a minha loja?',
             'resposta': 'Depois de iniciares sessão, usa a opção "Criar loja" e segue os passos.'},
        ]},
    },
    {
        'slug': 'termos', 'seccao': 'legal', 'ordem': 1, 'titulo': 'Termos de Serviço',
        'conteudo': (
            'Ao utilizar a plataforma, concordas com os presentes termos.\n\n'
            '## Utilização da plataforma\n'
            'A plataforma liga compradores a lojas independentes. Cada loja é responsável pelos seus produtos, preços, entregas e políticas de devolução.\n\n'
            '## Contas\n'
            'És responsável por manter a confidencialidade dos teus dados de acesso e por toda a actividade na tua conta.\n\n'
            '## Alterações\n'
            'Estes termos podem ser actualizados. A versão em vigor é sempre a publicada nesta página.'
        ),
        'dados': {},
    },
    {
        'slug': 'privacidade', 'seccao': 'legal', 'ordem': 2, 'titulo': 'Política de Privacidade',
        'conteudo': (
            'A tua privacidade é importante para nós.\n\n'
            '## Dados que recolhemos\n'
            '- Dados de conta: nome, email e telefone.\n'
            '- Dados de encomendas: produtos, moradas de entrega e pagamentos.\n\n'
            '## Como usamos os dados\n'
            'Usamos os teus dados apenas para processar encomendas, prestar suporte e melhorar o serviço.\n\n'
            '## Os teus direitos\n'
            'Podes pedir acesso, correcção ou eliminação dos teus dados através da página de contacto.'
        ),
        'dados': {},
    },
]


def criar(apps, schema_editor):
    Pagina = apps.get_model('app', 'PaginaInstitucional')
    for p in PAGINAS:
        Pagina.objects.get_or_create(slug=p['slug'], defaults=p)


def remover(apps, schema_editor):
    Pagina = apps.get_model('app', 'PaginaInstitucional')
    Pagina.objects.filter(slug__in=[p['slug'] for p in PAGINAS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0024_paginainstitucional'),
    ]

    operations = [
        migrations.RunPython(criar, remover),
    ]
