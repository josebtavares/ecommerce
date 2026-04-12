from django.db import migrations
 
 
def migrar_categorias_para_m2m(apps, schema_editor):
    Produto      = apps.get_model('app', 'Produto')
    CategoriaLoja = apps.get_model('app', 'CategoriaLoja')
 
    # agrupa produtos por loja e categoria
    for produto in Produto.objects.exclude(
        categoria=''
    ).exclude(categoria__isnull=True).select_related('loja'):
 
        nome = produto.categoria.lower().strip()
        if not nome:
            continue
 
        # cria ou recupera a categoria para esta loja
        cat, _ = CategoriaLoja.objects.get_or_create(
            loja=produto.loja,
            nome=nome,
            defaults={'ativo': True, 'icone': '📂'}
        )
 
        # associa o produto à categoria
        produto.categorias.add(cat)
 
    print(f'Migração concluída.')
 
 
def reverter_migração(apps, schema_editor):
    # devolve os dados ao campo texto (rollback)
    Produto = apps.get_model('app', 'Produto')
    for produto in Produto.objects.prefetch_related('categorias').all():
        cats = list(produto.categorias.values_list('nome', flat=True))
        if cats:
            produto.categoria = cats[0]  # primeiro nome como fallback
            produto.save(update_fields=['categoria'])
 
 
class Migration(migrations.Migration):
 
    # Substituir pelo número correcto das migrações anteriores
    dependencies = [
        ('app', '0015_alter_categoriadestaque_options_and_more'),
    ]
 
    operations = [
        migrations.RunPython(
            migrar_categorias_para_m2m,
            reverter_migração,
        ),
    ]