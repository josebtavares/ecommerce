from django.db import migrations


def corrigir(apps, schema_editor):
    """O arquivo fiscal segue o NIF: as contas que a 0014 pôs na loja ligada a um POS que vende com NIF próprio
    (não segue os dados da loja e tem outro NIF) voltam para o arquivo do POS — e as faturas registadas nelas também."""
    ContaMesa = apps.get_model('pos', 'ContaMesa')
    ConfiguracaoPOS = apps.get_model('pos', 'ConfiguracaoPOS')
    HistoricoFatura = apps.get_model('app', 'HistoricoFatura')
    for pos in ConfiguracaoPOS.objects.filter(loja_vinculada__isnull=False, fiscal_da_loja=False).select_related('loja_vinculada'):
        if pos.nif and pos.nif == pos.loja_vinculada.nif:
            continue
        contas = ContaMesa.objects.filter(pos=pos, loja=pos.loja_vinculada)
        HistoricoFatura.objects.filter(tipo='venda_pos', conta__in=contas).update(loja=None)
        contas.update(loja=None)


class Migration(migrations.Migration):

    dependencies = [
        ('pos', '0014_conta_loja'),
        ('app', '0063_faturas_vendas'),
    ]

    operations = [
        migrations.RunPython(corrigir, migrations.RunPython.noop),
    ]
