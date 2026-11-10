# A marca passa de Bende a Bendi e o domínio de bende.store a e-bendi.cv (2026-11-10).
# Muda o texto guardado na base de dados que aparece no site: páginas institucionais (termos, privacidade…),
# o rascunho da landing e a publicação em vigor. O histórico de publicações, os emails enviados, os avisos,
# os documentos fiscais e os backups ficam como estavam (são registo do que aconteceu).
import json
import re

from django.db import migrations

ARTIGOS = {'do': 'da', 'no': 'na', 'pelo': 'pela', 'ao': 'à', 'o': 'a',
           'Do': 'Da', 'No': 'Na', 'Pelo': 'Pela', 'Ao': 'À', 'O': 'A'}


def trocar(texto):
    if not isinstance(texto, str) or not texto:
        return texto
    t = re.sub(r'\b(do|no|pelo|ao|o|Do|No|Pelo|Ao|O) Bende\b', lambda m: ARTIGOS[m.group(1)] + ' Bendi', texto)
    t = re.sub(r'\bBende\b', 'Bendi', t)
    t = re.sub(r'\bBENDE\b', 'BENDI', t)
    return t.replace('www.bende.store', 'e-bendi.cv').replace('bende.store', 'e-bendi.cv')


def trocar_json(valor):
    if valor in (None, '', {}, []):
        return valor
    return json.loads(trocar(json.dumps(valor, ensure_ascii=False)))


def aplicar(apps, schema_editor):
    Pagina = apps.get_model('app', 'PaginaInstitucional')
    for p in Pagina.objects.all():
        novo = (trocar(p.titulo), trocar(p.conteudo), trocar_json(p.dados))
        if novo != (p.titulo, p.conteudo, p.dados):
            p.titulo, p.conteudo, p.dados = novo
            p.save(update_fields=['titulo', 'conteudo', 'dados'])

    Rascunho = apps.get_model('app', 'LandingRascunho')
    for r in Rascunho.objects.all():
        d = trocar_json(r.dados)
        if d != r.dados:
            r.dados = d
            r.save(update_fields=['dados'])

    Publicacao = apps.get_model('app', 'LandingPublicacao')
    ultima = Publicacao.objects.order_by('-publicado_em', '-pk').first()
    if ultima:
        d = trocar_json(ultima.dados)
        if d != ultima.dados:
            ultima.dados = d
            ultima.save(update_fields=['dados'])

    # os modelos da migração não disparam os sinais da cache pública: invalida-a à mão (a landing tem cache de 60 s)
    try:
        from app.utils.cache_publico import invalidar
        invalidar(tudo=True)
    except Exception:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0101_nome_bendi'),
    ]

    operations = [
        migrations.RunPython(aplicar, migrations.RunPython.noop),
    ]
