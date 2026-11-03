"""
Endereço público das lojas: /loja/<slug> (ex.: /loja/bom-sabor) em vez de /loja/<id>.

- Gerado do nome quando a loja é criada (Loja.save); o dono pode mudá-lo em Configurações.
- Os endereços antigos (LojaEnderecoAntigo) continuam a abrir a loja — redirecionam para o actual — e ficam
  reservados para ela: ninguém pode apanhar o link antigo de outra loja.
- /loja/<id> continua a funcionar (links antigos, notificações, backoffice) e redireciona também.
- O backoffice continua em /loja/<id>/backoffice (privado, não se partilha).
"""
import re
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.text import slugify

MIN, MAX = 3, 50
FORMATO = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
# palavras que são (ou podem vir a ser) páginas do site debaixo de /loja/
RESERVADOS = frozenset({
    'criar', 'nova', 'novo', 'demo', 'minhas', 'backoffice', 'admin', 'api', 'pos', 'loja', 'lojas',
    'bende', 'suporte', 'ajuda', 'editar', 'pesquisa', 'servicos', 'produto', 'produtos', 'checkout',
})
MAX_MUDANCAS, JANELA_DIAS = 3, 30


def normalizar(texto):
    """'Bom Sabor — Café!' → 'bom-sabor-cafe' (sem acentos, minúsculas, hífenes)."""
    return slugify(str(texto or ''))[:MAX].strip('-')


def _ocupado(slug, loja_id=None):
    from ..models import Loja, LojaEnderecoAntigo
    lojas = Loja.objects.filter(slug=slug)
    antigos = LojaEnderecoAntigo.objects.filter(slug=slug, ativo=True)      # os desligados pelo admin ficam livres
    if loja_id:
        lojas, antigos = lojas.exclude(pk=loja_id), antigos.exclude(loja_id=loja_id)
    return lojas.exists() or antigos.exists()


def gerar(nome, loja_id=None):
    """Endereço livre a partir do nome: 'bom-sabor', ou 'bom-sabor-2', 'bom-sabor-3'…"""
    base = normalizar(nome)
    if len(base) < MIN or base.isdigit() or base in RESERVADOS:
        base = normalizar(f'loja {base}') or 'loja'
    base = base[:MAX - 4].strip('-')
    slug, n = base, 1
    while _ocupado(slug, loja_id):
        n += 1
        slug = f'{base}-{n}'
    return slug


def erro_formato(slug):
    if len(slug) < MIN:
        return f'O endereço precisa de pelo menos {MIN} caracteres.'
    if len(slug) > MAX:
        return f'O endereço pode ter no máximo {MAX} caracteres.'
    if not FORMATO.match(slug):
        return 'Usa só letras minúsculas sem acentos, números e hífenes (ex.: bom-sabor).'
    if slug.isdigit():
        return 'O endereço precisa de ter pelo menos uma letra.'
    if slug in RESERVADOS:
        return 'Esse endereço está reservado pelo Bende. Escolhe outro.'
    return None


def validar(slug, loja, admin=False):
    """Mensagem de erro, ou None se a loja pode usar este endereço."""
    from ..models import LojaEnderecoAntigo
    e = erro_formato(slug)
    if e:
        return e
    if _ocupado(slug, loja.pk):
        return 'Esse endereço já é usado por outra loja.'
    # um endereço que o Bende retirou à loja (desligado pelo admin) — o dono não o pode voltar a pôr
    if not admin and LojaEnderecoAntigo.objects.filter(loja=loja, slug=slug, ativo=False).exists():
        return 'Esse endereço foi retirado pelo Bende. Escolhe outro.'
    return None


def mudancas_recentes(loja):
    """Mudanças do dono nos últimos JANELA_DIAS dias (as do admin não contam)."""
    from ..models import LojaEnderecoAntigo
    return LojaEnderecoAntigo.objects.filter(loja=loja, por_admin=False,
                                             criado_em__gte=timezone.now() - timedelta(days=JANELA_DIAS)).count()


def mudar(loja, novo, por=None, admin=False, manter_antigo=True, motivo=''):
    """
    Muda o endereço; o actual passa a antigo. Devolve a mensagem de erro ou None.
    admin=True: sem limite de mudanças e pode não manter o antigo (manter_antigo=False → deixa de abrir a loja e fica
    livre para outras). O dono mantém sempre o antigo.
    """
    novo = (novo if isinstance(novo, str) else '').strip().lower()
    try:
        return _mudar(loja, novo, por, admin, manter_antigo or not admin, (motivo or '')[:300])
    except IntegrityError:          # outra loja ficou com ele entretanto (dois pedidos ao mesmo tempo)
        return 'Esse endereço já é usado por outra loja.'


def _mudar(loja, novo, por, admin, manter_antigo, motivo):
    from ..models import Loja, LojaEnderecoAntigo
    with transaction.atomic():
        loja = Loja.objects.select_for_update().get(pk=loja.pk)
        if novo == loja.slug:
            return None
        e = validar(novo, loja, admin=admin)
        if e:
            return e
        if not admin and mudancas_recentes(loja) >= MAX_MUDANCAS:
            return f'Já mudaste o endereço {MAX_MUDANCAS} vezes nos últimos {JANELA_DIAS} dias. Tenta mais tarde.'
        LojaEnderecoAntigo.objects.create(loja=loja, slug=loja.slug, ativo=manter_antigo, por_admin=admin,
                                          alterado_por=por if getattr(por, 'pk', None) else None, motivo=motivo)
        loja.slug = novo
        loja.save(update_fields=['slug'])
    return None


def desligar(loja, slug):
    """Admin: um endereço antigo deixa de abrir a loja e fica livre (o registo fica). Devolve quantos desligou."""
    from ..models import LojaEnderecoAntigo
    return LojaEnderecoAntigo.objects.filter(loja=loja, slug=slug, ativo=True).update(ativo=False)


def historico(loja, n=30):
    """Admin: todas as mudanças (quem, quando, porquê, se o antigo ainda abre a loja)."""
    from ..models import LojaEnderecoAntigo
    return [{'slug': a.slug, 'criado_em': a.criado_em, 'ativo': a.ativo, 'por_admin': a.por_admin, 'motivo': a.motivo,
             'por': (a.alterado_por.get_full_name() or a.alterado_por.username) if a.alterado_por else ''}
            for a in LojaEnderecoAntigo.objects.filter(loja=loja).select_related('alterado_por')[:n]]


def resolver(ref):
    """'bom-sabor', um endereço antigo, ou '7' → a loja (ou None)."""
    from ..models import Loja, LojaEnderecoAntigo
    ref = str(ref or '').strip().lower()
    if not ref or len(ref) > 60:
        return None
    if ref.isascii() and ref.isdigit():
        return Loja.objects.filter(pk=int(ref)).first() if len(ref) < 12 else None
    loja = Loja.objects.filter(slug=ref).first()
    if loja:
        return loja
    antigo = LojaEnderecoAntigo.objects.select_related('loja').filter(slug=ref, ativo=True).order_by('-criado_em').first()
    return antigo.loja if antigo else None


def antigos(loja, n=20):
    """Endereços que a loja já usou (mais recentes primeiro), sem o actual."""
    from ..models import LojaEnderecoAntigo
    vistos = []
    for s in LojaEnderecoAntigo.objects.filter(loja=loja, ativo=True).exclude(slug=loja.slug).values_list('slug', flat=True):
        if s not in vistos:
            vistos.append(s)
    return vistos[:n]


def caminho(loja, produto_id=None):
    c = f'/loja/{loja.slug or loja.pk}'
    return f'{c}?produto={produto_id}' if produto_id else c
