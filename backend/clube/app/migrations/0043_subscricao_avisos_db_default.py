from django.db import migrations


class Migration(migrations.Migration):
    """Default na BD para avisos: o código antigo (sem o campo) continua a
    conseguir criar subscrições entre a migração e o deploy."""

    dependencies = [
        ('app', '0042_pos_subscricoes_carencia'),
    ]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE app_subscricao ALTER COLUMN avisos SET DEFAULT '[]'::jsonb;",
            "ALTER TABLE app_subscricao ALTER COLUMN avisos DROP DEFAULT;",
        ),
    ]
