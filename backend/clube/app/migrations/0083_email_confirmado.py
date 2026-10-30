from django.db import migrations, models


def confirmar_existentes(apps, schema_editor):
    # decisão de 2026-10-30: as contas que já existiam ficam confirmadas; só as novas têm de confirmar
    apps.get_model('app', 'Utilizador').objects.update(email_confirmado=True)


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0082_loja_demo'),
    ]

    operations = [
        migrations.AddField(
            model_name='utilizador',
            name='email_confirmado',
            field=models.BooleanField(db_default=False, default=False),
        ),
        migrations.AddField(
            model_name='utilizador',
            name='email_confirmado_em',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(confirmar_existentes, migrations.RunPython.noop),
    ]
