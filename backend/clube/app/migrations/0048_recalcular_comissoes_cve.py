"""
Depois da conversão para escudos (0047), as comissões guardavam o arredondamento feito em euros
multiplicado por 110 (10% de 12,98 € = 1,30 € → 143$34, quando 10% de 1.431$24 = 143$12).
Recalcula-as a partir do valor da encomenda em escudos, como Comissao.registar faz.
"""
from decimal import Decimal

from django.db import migrations


def recalcular(apps, schema_editor):
    Comissao = apps.get_model('app', 'Comissao')
    for c in Comissao.objects.all().only('pk', 'valor_encomenda', 'percentagem', 'valor_comissao').iterator():
        certo = (c.valor_encomenda * c.percentagem / 100).quantize(Decimal('0.01'))
        if certo != c.valor_comissao:
            Comissao.objects.filter(pk=c.pk).update(valor_comissao=certo)


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0047_converter_valores_cve'),
    ]

    operations = [
        migrations.RunPython(recalcular, migrations.RunPython.noop),
    ]
