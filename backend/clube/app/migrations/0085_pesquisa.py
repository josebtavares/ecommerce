import django.contrib.postgres.indexes
import django.contrib.postgres.search
import django.db.models.deletion
from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0084_entrega_cancelada_motivo'),
    ]

    operations = [
        TrigramExtension(),     # pg_trgm: extensão "trusted" do Postgres, vem com a imagem
        migrations.CreateModel(
            name='EntradaPesquisa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('produto', 'Produto'), ('loja', 'Loja'), ('servico', 'Serviço')], max_length=8)),
                ('objeto_id', models.PositiveIntegerField()),
                ('nome', models.CharField(max_length=200)),
                ('nome_norm', models.CharField(max_length=200)),
                ('texto_a', models.TextField(blank=True, default='')),
                ('texto_b', models.TextField(blank=True, default='')),
                ('texto_c', models.TextField(blank=True, default='')),
                ('vetor', django.contrib.postgres.search.SearchVectorField(null=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
                ('loja', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='app.loja')),
            ],
            options={
                'indexes': [
                    django.contrib.postgres.indexes.GinIndex(fields=['vetor'], name='pesquisa_vetor_gin'),
                    django.contrib.postgres.indexes.GinIndex(fields=['nome_norm'], name='pesquisa_nome_trgm', opclasses=['gin_trgm_ops']),
                ],
                'constraints': [models.UniqueConstraint(fields=('tipo', 'objeto_id'), name='pesquisa_entrada_unica')],
            },
        ),
    ]
