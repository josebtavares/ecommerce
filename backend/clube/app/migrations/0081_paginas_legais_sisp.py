from django.db import migrations


# Rascunhos completos das páginas legais para o contrato SISP (MD050.03, cl.3: limitação de responsabilidade,
# privacidade, devoluções, transmissão segura dos dados do cartão, moeda). Revê-os com um jurista em Admin → Páginas.
# Só substituem as páginas que ninguém editou no painel (atualizado_por vazio) — o texto escrito por um admin fica.
PAGINAS = {
    'termos': (
        'Estes termos regulam a utilização da Bende (bende.store), a plataforma que liga compradores a lojas '
        'independentes em Cabo Verde. A entidade que explora a plataforma está identificada no rodapé do site, '
        'com o respetivo NIF. Ao criares conta ou fazeres uma encomenda, aceitas estes termos.\n\n'
        '## O que é a Bende\n'
        '- A Bende é uma montra: cada loja vende em nome próprio. O contrato de compra e venda é entre ti e a loja.\n'
        '- Cada loja é responsável pelos seus produtos e serviços, pelas descrições, pelos preços, pelo stock, pela '
        'entrega, pela fatura e pelas devoluções. Os dados de cada loja (nome, NIF, morada, email e telefone) estão '
        'em "Vendido por", na página da loja e no checkout.\n'
        '- A Bende cobra às lojas uma comissão ou uma mensalidade pelo uso da plataforma. O comprador não paga nada à '
        'Bende.\n\n'
        '## Contas\n'
        '- Para comprar precisas de uma conta com nome, email, telefone e morada verdadeiros. És responsável por '
        'manter a password em segredo e por tudo o que é feito na tua conta.\n'
        '- Podemos suspender ou fechar contas usadas para fraude, abuso ou em violação destes termos.\n\n'
        '## Preços e moeda\n'
        '- Todos os preços estão em escudos cabo-verdianos (CVE) e incluem os impostos aplicáveis, salvo indicação da '
        'loja. O custo da entrega é mostrado no checkout antes de confirmares.\n'
        '- Pagar com cartão não tem nenhum custo adicional.\n\n'
        '## Pagamentos\n'
        '- Podes pagar como a loja aceitar: em dinheiro na entrega ou levantamento, por transferência, ou com cartão.\n'
        '- O pagamento com cartão é feito na página segura da SISP (rede vinti4), com 3-D Secure, diretamente à loja, '
        'que tem contrato próprio com a SISP. Os dados do teu cartão são introduzidos e tratados apenas pela SISP: '
        'a Bende e a loja nunca os veem nem os guardam. Toda a comunicação com o site é cifrada (HTTPS).\n'
        '- Depois do pagamento recebes o comprovativo na encomenda (referência da transação, data, valor e loja). '
        'A fatura legal é emitida pela loja.\n'
        '- Uma encomenda com pagamento online que não seja paga em 30 minutos é cancelada e o stock é libertado.\n\n'
        '## Entregas, devoluções e reembolsos\n'
        'Aplicam-se as políticas de cada loja e, quando a loja não indica outra coisa, as páginas Entregas e '
        'Devoluções e reembolsos da Bende. Um reembolso de um pagamento com cartão é feito para o mesmo cartão.\n\n'
        '## Utilização aceitável\n'
        'Não podes usar a plataforma para atividades ilegais, fraude, publicar conteúdos ofensivos ou enganosos, nem '
        'tentar aceder a contas ou dados de terceiros. As lojas não podem vender produtos proibidos por lei.\n\n'
        '## Limitação de responsabilidade\n'
        '- A Bende não é parte na venda e não responde pelos produtos, serviços, entregas ou garantias das lojas, nem '
        'por danos resultantes da sua utilização, sem prejuízo dos direitos que a lei te dá como consumidor.\n'
        '- A Bende faz o possível por manter a plataforma disponível e segura, mas não garante um funcionamento sem '
        'interrupções nem responde por falhas de terceiros (rede de pagamentos, operadores de telecomunicações, '
        'alojamento) ou de força maior.\n'
        '- Nada nestes termos exclui a responsabilidade que a lei não permita excluir, nomeadamente por dolo ou culpa '
        'grave.\n\n'
        '## Reclamações\n'
        'Fala primeiro com a loja (contactos em "Vendido por"). Se não resolver, contacta a Bende pela página de '
        'contacto — ajudamos a mediar. Podes ainda recorrer às entidades de defesa do consumidor.\n\n'
        '## Lei aplicável e alterações\n'
        '- Estes termos regem-se pela lei de Cabo Verde. Para qualquer litígio são competentes os tribunais de Cabo '
        'Verde, sem prejuízo das regras que protegem o consumidor.\n'
        '- Podemos atualizar estes termos. A versão em vigor é a publicada nesta página, com a data da última '
        'alteração; as encomendas já feitas seguem os termos aceites nesse momento.'
    ),
    'privacidade': (
        'Esta política explica que dados pessoais a Bende recolhe, para quê e quais são os teus direitos, nos termos '
        'da lei de proteção de dados pessoais de Cabo Verde. O responsável pelo tratamento é a entidade que explora a '
        'plataforma, identificada no rodapé do site.\n\n'
        '## Dados que recolhemos\n'
        '- Conta: nome, nome de utilizador, email, telefone, morada e, se quiseres, foto.\n'
        '- Encomendas e marcações: produtos ou serviços, moradas de entrega, notas, estado e histórico.\n'
        '- Pagamentos: método, valor, data e a referência da transação. Os dados do cartão (número, validade, código) '
        'são introduzidos apenas na página da SISP — a Bende nunca os recebe nem os guarda.\n'
        '- Conversas no chat de suporte e com as lojas, avaliações e pedidos de devolução.\n'
        '- Dados técnicos: endereço IP e registos de acesso, usados para segurança e para detetar abusos.\n\n'
        '## Para que usamos os dados\n'
        '- Criar e gerir a tua conta, processar encomendas, marcações, pagamentos, entregas e reembolsos.\n'
        '- Dar suporte, prevenir fraude e cumprir obrigações legais e fiscais.\n'
        '- Enviar avisos sobre as tuas encomendas. Não enviamos publicidade sem o teu consentimento.\n\n'
        '## Com quem partilhamos\n'
        '- A loja onde compras recebe o teu nome, telefone, email e morada de entrega, para preparar e entregar a '
        'encomenda e emitir a fatura.\n'
        '- A SISP recebe os dados necessários ao pagamento com cartão, incluindo nome, email e telefone.\n'
        '- Prestadores que trabalham para nós (alojamento, armazenamento, envio de email), obrigados a confidencialidade.\n'
        '- Autoridades, quando a lei o exige. Não vendemos dados pessoais.\n\n'
        '## Durante quanto tempo\n'
        'Guardamos os dados enquanto tiveres conta. Os registos de encomendas, pagamentos e faturas ficam pelo prazo '
        'que a lei fiscal e comercial exige. Ao eliminares a conta, os restantes dados são apagados ou anonimizados.\n\n'
        '## Segurança\n'
        'Toda a comunicação é cifrada (HTTPS). As passwords são guardadas de forma irreversível (hash), os acessos '
        'aos dados são limitados a quem precisa deles e as cópias de segurança ficam em armazenamento privado.\n\n'
        '## Cookies e armazenamento local\n'
        'Usamos apenas o armazenamento do browser necessário ao funcionamento do site (sessão iniciada, carrinho, '
        'tema claro/escuro). Não usamos cookies de publicidade.\n\n'
        '## Os teus direitos\n'
        '- Podes pedir acesso, correção, oposição ou eliminação dos teus dados. Corriges os teus dados no perfil; '
        'os outros pedidos fazes pela página de contacto.\n'
        '- Podes apresentar queixa à Comissão Nacional de Proteção de Dados (CNPD) de Cabo Verde.\n\n'
        '## Alterações\n'
        'Podemos atualizar esta política. A versão em vigor é a publicada nesta página.'
    ),
}


def migrar(apps, schema_editor):
    Pagina = apps.get_model('app', 'PaginaInstitucional')
    for slug, conteudo in PAGINAS.items():
        Pagina.objects.filter(slug=slug, atualizado_por__isnull=True).update(conteudo=conteudo)


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0080_cobrar_comissoes_desde'),
    ]

    operations = [
        migrations.RunPython(migrar, migrations.RunPython.noop),
    ]
