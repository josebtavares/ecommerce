"""
Estatísticas da barra de pesquisa (fase 3): o que os clientes procuram, o que não encontram e onde clicam.

- registar(): o browser manda uma linha por pesquisa "assente" (viu os resultados e parou de escrever, ou
  clicou). A mesma `id_cliente` actualiza a linha (afinações "cam" → "camisola", e o clique a seguir).
- estatisticas(dias): o resumo para Admin → Pesquisas.
- limpar(): apaga o que tem mais de DIAS_REGISTO dias (worker).
Sem utilizador nem IP — só um id aleatório do separador do browser.
"""
import re
from datetime import timedelta

from django.db.models import Avg, Count, Max, Q
from django.db.models.functions import TruncDate
from django.utils import timezone

DIAS_REGISTO = 180
JANELA_ATUALIZAR = timedelta(minutes=30)     # depois disto a linha já não muda (nem com o mesmo id)
TIPOS_CLIQUE = ('produto', 'loja', 'servico', 'categoria', 'ver_todos')
PERIODOS = (7, 30, 90)


def _id_valido(v):
    return isinstance(v, str) and re.fullmatch(r'[A-Za-z0-9-]{8,40}', v) is not None


def registar(dados):
    """→ None se aceitou, ou o motivo (texto) se recusou. Nunca rebenta com dados estranhos."""
    from ..models import RegistoPesquisa
    from .pesquisa import normalizar
    if not isinstance(dados, dict):
        return 'pedido inválido'
    id_cliente, sessao = dados.get('id'), dados.get('sessao')
    if not _id_valido(id_cliente) or not _id_valido(sessao):
        return 'id inválido'
    texto = str(dados.get('q') or '').strip()[:80]
    q = normalizar(texto, juntar=False)[:80]
    if len(q.replace(' ', '')) < 2:
        return 'pesquisa curta'
    origem = dados.get('origem') if dados.get('origem') in ('caixa', 'pagina') else 'caixa'
    try:
        resultados = max(0, min(int(dados.get('resultados') or 0), 100000))
    except (TypeError, ValueError):
        return 'resultados inválidos'
    clique = dados.get('clique') if isinstance(dados.get('clique'), dict) else None
    campos = {'q': q, 'texto': texto, 'origem': origem, 'resultados': resultados}
    if clique and clique.get('tipo') in TIPOS_CLIQUE:
        try:
            cid = int(clique['id']) if clique.get('id') not in (None, '') else None
            pos = int(clique['posicao']) if clique.get('posicao') not in (None, '') else None
        except (TypeError, ValueError):
            cid = pos = None
        campos.update(clique_tipo=clique['tipo'], clique_id=cid if cid and 0 < cid < 2**31 else None,
                      clique_nome=str(clique.get('nome') or '')[:120],
                      clique_posicao=pos if pos is not None and 0 <= pos < 1000 else None)

    r = RegistoPesquisa.objects.filter(id_cliente=id_cliente).first()
    if r is None:
        RegistoPesquisa.objects.create(id_cliente=id_cliente, sessao=sessao, **campos)
        return None
    if r.sessao != sessao or timezone.now() - r.criado_em > JANELA_ATUALIZAR:
        return 'não pode mudar este registo'
    # fica o primeiro clique (a posição diz o que importa) — excepto "ver todos": o clique a seguir, já na
    # página de resultados, diz mais e substitui-o
    if r.clique_tipo and 'clique_tipo' in campos and not (r.clique_tipo == 'ver_todos' and campos['clique_tipo'] != 'ver_todos'):
        for k in ('clique_tipo', 'clique_id', 'clique_nome', 'clique_posicao'):
            campos.pop(k)
    if r.clique_tipo and campos['q'] != r.q:
        return None                                    # já clicou: uma nova pesquisa tem outro id
    for k, v in campos.items():
        setattr(r, k, v)
    r.save()
    return None


def limpar():
    from ..models import RegistoPesquisa
    return RegistoPesquisa.objects.filter(criado_em__lt=timezone.now() - timedelta(days=DIAS_REGISTO)).delete()[0]


def _nomes_clicados(linhas):
    """Nome actual dos produtos/lojas/serviços clicados (o índice tem-no); senão o que veio no registo."""
    from ..models import EntradaPesquisa
    pares = {(l['clique_tipo'], l['clique_id']) for l in linhas if l['clique_id']}
    nomes = {}
    if pares:
        q = Q()
        for t, i in pares:
            q |= Q(tipo=t, objeto_id=i)
        nomes = {(e.tipo, e.objeto_id): (e.nome, e.loja_id) for e in EntradaPesquisa.objects.filter(q).only('tipo', 'objeto_id', 'nome', 'loja_id')}
    return nomes


def estatisticas(dias=30):
    from ..models import RegistoPesquisa
    from .horarios import fuso
    dias = dias if dias in PERIODOS else 30
    desde = timezone.now() - timedelta(days=dias)
    qs = RegistoPesquisa.objects.filter(criado_em__gte=desde)
    tem_clique = ~Q(clique_tipo='')

    total = qs.count()
    sem = qs.filter(resultados=0).count()
    com_resultados = total - sem
    cliques = qs.filter(tem_clique).count()
    resumo = {
        'total': total,
        'sessoes': qs.values('sessao').distinct().count(),
        'sem_resultados': sem,
        'taxa_sem_resultados': round(100 * sem / total, 1) if total else None,
        'com_clique': cliques,
        'taxa_clique': round(100 * qs.filter(tem_clique, resultados__gt=0).count() / com_resultados, 1) if com_resultados else None,
        'na_pagina': qs.filter(origem='pagina').count(),
    }

    por_dia = list(qs.annotate(dia=TruncDate('criado_em', tzinfo=fuso())).values('dia')
                   .annotate(total=Count('id'), sem_resultados=Count('id', filter=Q(resultados=0)))
                   .order_by('dia'))
    # dias sem pesquisas também aparecem (o gráfico não salta dias)
    hoje = timezone.localtime(timezone.now(), fuso()).date()
    por_data = {l['dia']: l for l in por_dia}
    serie = []
    for k in range(dias - 1, -1, -1):
        d = hoje - timedelta(days=k)
        l = por_data.get(d, {})
        serie.append({'dia': d.isoformat(), 'total': l.get('total', 0), 'sem_resultados': l.get('sem_resultados', 0)})

    def grupo(base, n, ordem='-total'):
        return [
            {'q': l['q'], 'texto': l['texto'], 'total': l['total'], 'sessoes': l['sessoes'],
             'cliques': l['cliques'], 'resultados': round(l['media'] or 0, 1),
             'ultima': timezone.localtime(l['ultima'], fuso()).strftime('%d/%m %H:%M')}
            for l in base.values('q').annotate(
                texto=Max('texto'), total=Count('id'), sessoes=Count('sessao', distinct=True),
                cliques=Count('id', filter=tem_clique), media=Avg('resultados'), ultima=Max('criado_em'),
            ).order_by(ordem, 'q')[:n]
        ]

    sem_clique = [g for g in grupo(qs.filter(resultados__gt=0), 60) if not g['cliques'] and g['total'] >= 2][:15]

    clicados = list(qs.filter(tem_clique).exclude(clique_tipo='ver_todos')
                    .values('clique_tipo', 'clique_id', 'clique_nome').annotate(total=Count('id'))
                    .order_by('-total', 'clique_tipo')[:40])
    nomes = _nomes_clicados(clicados)
    juntos = {}
    for l in clicados:
        chave = (l['clique_tipo'], l['clique_id'] or l['clique_nome'])
        atual = nomes.get((l['clique_tipo'], l['clique_id']))
        j = juntos.setdefault(chave, {'tipo': l['clique_tipo'], 'id': l['clique_id'],
                                      'nome': atual[0] if atual else (l['clique_nome'] or '—'),
                                      'loja_id': atual[1] if atual else None,
                                      'existe': bool(atual) or l['clique_tipo'] == 'categoria', 'total': 0})
        j['total'] += l['total']
    mais_clicados = sorted(juntos.values(), key=lambda j: (-j['total'], j['nome']))[:15]

    return {
        'dias': dias, 'resumo': resumo, 'por_dia': serie,
        'top': grupo(qs, 30),
        'sem_resultados': grupo(qs.filter(resultados=0), 30),
        'sem_clique': sem_clique,
        'mais_clicados': mais_clicados,
    }
