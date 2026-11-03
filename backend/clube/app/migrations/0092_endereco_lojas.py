# Endereço público das lojas (/loja/<slug>): campo Loja.slug, gerado do nome para as lojas que já existem
# (mais antigas primeiro ficam com o nome "limpo"; repetidos levam -2, -3…), e LojaEnderecoAntigo.
import django.db.models.deletion
from django.db import migrations, models
from django.utils.text import slugify

RESERVADOS = {
    'criar', 'nova', 'novo', 'demo', 'minhas', 'backoffice', 'admin', 'api', 'pos', 'loja', 'lojas',
    'bende', 'suporte', 'ajuda', 'editar', 'pesquisa', 'servicos', 'produto', 'produtos', 'checkout',
}


def preencher(apps, schema_editor):
    Loja = apps.get_model('app', 'Loja')
    usados = set()
    for loja in Loja.objects.order_by('data_criacao', 'pk').only('pk', 'nome'):
        base = slugify(loja.nome or '')[:50].strip('-')
        if len(base) < 3 or base.isdigit() or base in RESERVADOS:
            base = slugify(f'loja {base}')[:50].strip('-') or 'loja'
        base = base[:46].strip('-')
        slug, n = base, 1
        while slug in usados:
            n += 1
            slug = f'{base}-{n}'
        usados.add(slug)
        Loja.objects.filter(pk=loja.pk).update(slug=slug)


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0091_arquivo_fiscal'),
    ]

    operations = [
        migrations.AddField(
            model_name='loja',
            name='slug',
            field=models.SlugField(max_length=60, null=True, db_index=False),
        ),
        migrations.RunPython(preencher, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='loja',
            name='slug',
            field=models.SlugField(max_length=60, unique=True),
        ),
        migrations.CreateModel(
            name='LojaEnderecoAntigo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(max_length=60)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('loja', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enderecos_antigos', to='app.loja')),
            ],
            options={'ordering': ['-criado_em']},
        ),
    ]
