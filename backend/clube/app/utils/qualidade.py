"""
Qualidade do catálogo (Admin → Catálogo): o que a SISP/o banco notam ao rever o site, loja a loja.

• Produtos: os requisitos da prontidão (foto, preço, descrição — prontidao.faltas_produto) e avisos que não
  bloqueiam nada: nome provisório ("teste", "asdf", "produto 1"…), preço estranho (abaixo de PRECO_MIN ou acima de
  PRECO_MAX) e o mesmo nome repetido na loja.
• Lojas: os requisitos para publicar que faltam (prontidao.py), sem logótipo, descrição curta, sem nada à venda.
• Só lojas activas e pendentes (as fechadas/suspensas não aparecem ao público). As lojas demo (Loja.demo,
  marcada pelo admin) vêm marcadas — vão ser escondidas antes da revisão.
• "Avisar a loja": notificação ao dono com o resumo (no máximo uma por dia por loja).
Só lê — não esconde nem altera nada.
"""
import re
import unicodedata
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count
from django.utils import timezone

from . import prontidao

PRECO_MIN = Decimal('20')            # CVE — abaixo disto quase sempre é engano ou teste
PRECO_MAX = Decimal('2000000')
INTERVALO_AVISO = timedelta(hours=24)

NOMES_PROVISORIOS = re.compile(
    r'^(?:teste?s?|test(?:ing)?|asdf\w*|qwer\w*|xx+|aa+|abc|lorem\b.*|exemplo|sem nome|novo produto|produto|'
    r'produto\s*\d+|item\s*\d*|untitled|placeholder|\d+)$')

TITULOS = {
    'foto': 'Sem foto',
    'descricao': 'Descrição curta',
    'preco': 'Sem preço',
    'nome': 'Nome provisório',
    'preco_estranho': 'Preço estranho',
    'duplicado': 'Nome repetido',
}
AVISOS_LOJA = {
    'logo': 'Sem logótipo',
    'descricao_loja': 'Descrição da loja curta',
    'vazia': 'Nada à venda',
}


def _normalizar(nome):
    t = unicodedata.normalize('NFKD', str(nome or '')).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', ' ', t)).strip()


def nome_provisorio(nome):
    n = _normalizar(nome)
    return len(n) < 3 or bool(NOMES_PROVISORIOS.match(n))


def problemas_produto(p, n_imagens=None, repetidos=frozenset()):
    """[chave] — as faltas da prontidão (com as chaves daqui) + os avisos."""
    mapa = {'foto': 'foto', 'descrição': 'descricao', 'preço': 'preco'}
    out = [mapa[f] for f in prontidao.faltas_produto(p, n_imagens)]
    if nome_provisorio(p.nome):
        out.append('nome')
    if p.preco and (p.preco < PRECO_MIN or p.preco > PRECO_MAX):
        out.append('preco_estranho')
    if _normalizar(p.nome) in repetidos:
        out.append('duplicado')
    return out


def _produtos(loja):
    from ..models import Produto
    qs = (Produto.objects.filter(loja=loja, ativo=True).annotate(n_imagens=Count('imagens'))
          .only('id', 'nome', 'descricao', 'preco', 'ficheiro'))
    lista = list(qs)
    vistos, repetidos = set(), set()
    for p in lista:
        n = _normalizar(p.nome)
        (repetidos if n in vistos else vistos).add(n)
    return [(p, problemas_produto(p, p.n_imagens, repetidos)) for p in lista]


def e_demo(loja):
    return loja.demo


def ultimo_aviso(loja):
    from ..models import Notificacao
    n = Notificacao.objects.filter(loja=loja, tipo='qualidade_catalogo').order_by('-data_criacao').first()
    return n.data_criacao if n else None


def analisar_loja(loja, com_produtos=False):
    pront = prontidao.avaliar(loja)
    produtos = _produtos(loja)
    por_tipo = {}
    for _, probs in produtos:
        for c in probs:
            por_tipo[c] = por_tipo.get(c, 0) + 1
    avisos = [{'chave': r['chave'], 'titulo': r['titulo']} for r in pront['requisitos'] if not r['ok']]
    # sem nenhum produto activo (nem serviços): o requisito do produto diz-se "Nada à venda" (conta uma vez só)
    if not produtos:
        for a in avisos:
            if a['chave'] == 'produto':
                a['chave'], a['titulo'] = 'vazia', AVISOS_LOJA['vazia']
    if not loja.logo:
        avisos.append({'chave': 'logo', 'titulo': AVISOS_LOJA['logo']})
    if len((loja.descricao or '').strip()) < prontidao.DESCRICAO_MIN:
        avisos.append({'chave': 'descricao_loja', 'titulo': AVISOS_LOJA['descricao_loja']})
    com_problemas = sum(1 for _, probs in produtos if probs)
    out = {
        'id': loja.id, 'nome': loja.nome, 'estado': loja.estado, 'demo': e_demo(loja),
        'percentagem': pront['percentagem'], 'completa': pront['completa'],
        'avisos': avisos,
        'produtos_total': len(produtos), 'produtos_com_problemas': com_problemas,
        'por_tipo': por_tipo,
        # "pontos" ordena a lista: requisitos e avisos da loja pesam mais que cada produto
        'pontos': 3 * len(avisos) + com_problemas,
    }
    if com_produtos:
        out['produtos'] = [{'id': p.id, 'nome': p.nome, 'preco': str(p.preco),
                            'problemas': [{'chave': c, 'titulo': TITULOS[c]} for c in probs]}
                           for p, probs in produtos if probs][:300]
    return out


def analisar(estado=None, incluir_demo=True):
    from ..models import Loja
    qs = Loja.objects.filter(estado__in=[estado] if estado in ('ativa', 'pendente') else ['ativa', 'pendente'])
    qs = qs.select_related('dono__user', 'config_servicos').order_by('nome')[:500]
    lojas = [analisar_loja(l) for l in qs]
    if not incluir_demo:
        lojas = [l for l in lojas if not l['demo']]
    lojas.sort(key=lambda l: (-l['pontos'], l['nome'].lower()))
    por_tipo = {}
    for l in lojas:
        for c, n in l['por_tipo'].items():
            por_tipo[c] = por_tipo.get(c, 0) + n
    return {
        'resumo': {
            'lojas': len(lojas),
            'lojas_com_problemas': sum(1 for l in lojas if l['pontos']),
            'lojas_incompletas': sum(1 for l in lojas if not l['completa']),
            'demo': sum(1 for l in lojas if l['demo']),
            'produtos': sum(l['produtos_total'] for l in lojas),
            'produtos_com_problemas': sum(l['produtos_com_problemas'] for l in lojas),
            'por_tipo': [{'chave': c, 'titulo': TITULOS[c], 'total': por_tipo.get(c, 0)} for c in TITULOS],
        },
        'lojas': lojas,
    }


def texto_aviso(r):
    """Mensagem para o dono (r = analisar_loja)."""
    partes = []
    if r['avisos']:
        partes.append('Na loja: ' + '; '.join(a['titulo'].lower() for a in r['avisos']) + '.')
    if r['produtos_com_problemas']:
        tipos = ', '.join(f"{TITULOS[c].lower()} ({n})" for c, n in sorted(r['por_tipo'].items(), key=lambda x: -x[1]))
        partes.append(f"{r['produtos_com_problemas']} produto(s) a rever: {tipos}.")
    return ('A equipa da Bende reviu a tua loja. ' + ' '.join(partes)
            + ' Vê os detalhes na barra do topo do backoffice da loja.')


def avisar(loja):
    """→ (enviado, data do último aviso). Uma notificação por dia, no máximo (a loja fica bloqueada enquanto se
    decide: dois cliques seguidos não mandam duas)."""
    from django.db import transaction
    from ..models import Loja
    from ..Views.notificacaoView import notificar
    with transaction.atomic():
        Loja.objects.select_for_update().filter(pk=loja.pk).first()
        ultimo = ultimo_aviso(loja)
        if ultimo and timezone.now() - ultimo < INTERVALO_AVISO:
            return False, ultimo
        r = analisar_loja(loja)
        if not r['pontos']:
            return False, None
        notificar(loja.dono, 'qualidade_catalogo', 'Melhora a tua loja', texto_aviso(r), loja=loja,
                  link=f'/loja/{loja.id}/backoffice')
        return True, ultimo_aviso(loja)


def avisos_backoffice(loja):
    """Para a barra da prontidão: avisos que não bloqueiam — da loja (logótipo, descrição) e dos produtos
    (nome provisório, preço estranho, repetido)."""
    loja_avisos = []
    if not loja.logo:
        loja_avisos.append({'chave': 'logo', 'titulo': 'Põe o logótipo da loja', 'seccao': 'configuracoes'})
    if len((loja.descricao or '').strip()) < prontidao.DESCRICAO_MIN:
        loja_avisos.append({'chave': 'descricao_loja', 'titulo': 'Escreve uma descrição da loja (pelo menos '
                            f'{prontidao.DESCRICAO_MIN} caracteres)', 'seccao': 'configuracoes'})
    lista = [{'id': p.id, 'nome': p.nome, 'avisos': [TITULOS[c].lower() for c in probs if c in ('nome', 'preco_estranho', 'duplicado')]}
             for p, probs in _produtos(loja)]
    lista = [x for x in lista if x['avisos']]
    return {'loja': loja_avisos, 'total': len(lista), 'produtos': lista[:prontidao.MAX_INCOMPLETOS]}
