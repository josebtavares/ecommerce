from django.db import migrations, models
from django.db.models import F, OuterRef, Subquery
from django.db.models.functions import Coalesce


def preencher(apps, schema_editor):
    """Pagamentos já recebidos: cartão na criação; dinheiro quando a encomenda foi concluída."""
    Pagamento = apps.get_model('app', 'Pagamento')
    Encomenda = apps.get_model('app', 'Encomenda')
    conclusao = Subquery(Encomenda.objects.filter(id=OuterRef('encomenda_id')).values('data_conclusao')[:1])
    pagos = Pagamento.objects.filter(status__in=['aprovado', 'reembolsado', 'reembolsado_parcial'],
                                     data_pagamento__isnull=True)
    pagos.filter(referencia_transacao='dinheiro').update(
        data_pagamento=Coalesce(conclusao, F('data_criacao')))
    pagos.exclude(referencia_transacao='dinheiro').update(data_pagamento=F('data_criacao'))


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0052_reembolso_confirmacao'),
    ]

    operations = [
        migrations.AddField(
            model_name='pagamento',
            name='data_pagamento',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.RunPython(preencher, migrations.RunPython.noop),
    ]
