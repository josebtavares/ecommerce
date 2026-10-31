from django.db import migrations, models


def fechar_entregas_de_canceladas(apps, schema_editor):
    """Encomendas já canceladas cuja entrega ficou aberta (o condutor continuava a vê-las por entregar)."""
    Entrega = apps.get_model('app', 'Entrega')
    Entrega.objects.filter(encomenda__status='cancelado', status__in=['atribuido', 'a_caminho']).update(status='cancelada')


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0083_email_confirmado'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entrega',
            name='status',
            field=models.CharField(choices=[('atribuido', 'Atribuído'), ('a_caminho', 'A caminho'), ('entregue', 'Entregue'), ('falhou', 'Falhou'), ('cancelada', 'Cancelada')], default='atribuido', max_length=15),
        ),
        migrations.AddField(
            model_name='entrega',
            name='motivo_falha',
            field=models.CharField(blank=True, choices=[('cliente_ausente', 'Cliente ausente'), ('sem_contacto', 'Cliente não atende'), ('morada_errada', 'Morada errada ou incompleta'), ('recusada', 'O cliente recusou'), ('outro', 'Outro motivo')], default='', max_length=20),
        ),
        migrations.AddField(
            model_name='entrega',
            name='nota_falha',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        migrations.RunPython(fechar_entregas_de_canceladas, migrations.RunPython.noop),
    ]
