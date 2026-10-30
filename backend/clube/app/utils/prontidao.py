"""Loja pronta para ser publicada: os requisitos que a SISP/o banco esperam ver numa loja do marketplace
(quem vende, contactos, políticas e pelo menos um produto ou serviço bem apresentado; com pagamentos online
a sério e cartão/mobile money ligados, também os dados bancários).

Qualquer pessoa cria a loja incompleta; o backoffice mostra a barra de progresso e o que falta,
e o admin só aprova (publica) uma loja pendente com todos os requisitos cumpridos.
As lojas já activas não são afectadas — só vêem os avisos.
"""
import re

from django.db.models import Count

DESCRICAO_MIN = 20           # caracteres de uma descrição "a sério"
MAX_INCOMPLETOS = 50         # produtos incompletos listados no backoffice


def faltas_produto(p, n_imagens=None):
    """O que falta a um produto para ficar bem apresentado (lista vazia = completo)."""
    faltas = []
    imagens = n_imagens if n_imagens is not None else p.imagens.count()
    if not p.ficheiro and not imagens:
        faltas.append('foto')
    if len((p.descricao or '').strip()) < DESCRICAO_MIN:
        faltas.append('descrição')
    if not p.preco or p.preco <= 0:
        faltas.append('preço')
    return faltas


def _servico_completo(s):
    return s.preco is not None and len((s.descricao or '').strip()) >= DESCRICAO_MIN and (s.preco > 0 or s.tipo_preco != 'fixo')


def avaliar(loja, com_produtos=False):
    """{ percentagem, completa, requisitos: [{chave, titulo, ok, ajuda, seccao}], produtos_incompletos? }"""
    from ..models import Produto
    produtos = (Produto.objects.filter(loja=loja, ativo=True)
                .annotate(n_imagens=Count('imagens')).only('id', 'nome', 'descricao', 'preco', 'ficheiro'))
    completos = incompletos = 0
    lista = []
    for p in produtos:
        f = faltas_produto(p, p.n_imagens)
        if f:
            incompletos += 1
            if len(lista) < MAX_INCOMPLETOS:
                lista.append({'id': p.id, 'nome': p.nome, 'faltas': f})
        else:
            completos += 1
    servicos_ok = False
    cfg = getattr(loja, 'config_servicos', None)
    if not completos and cfg and cfg.ativo:        # módulo desligado: os serviços não aparecem ao público
        from ..servicos.models import Servico
        servicos_ok = any(_servico_completo(s) for s in Servico.objects.filter(loja=loja, ativo=True, visivel=True))

    entrega = loja.entrega_ativa
    requisitos = [
        {'chave': 'nif', 'titulo': 'NIF da loja', 'seccao': 'configuracoes',
         'ok': bool(re.fullmatch(r'\d{9}', loja.nif or '')),
         'ajuda': 'Em Configurações → Dados fiscais (só o dono).'},
        {'chave': 'localizacao', 'titulo': 'Localização', 'seccao': 'configuracoes',
         'ok': bool((loja.localizacao or '').strip()),
         'ajuda': 'A morada ou zona da loja, em Configurações → Informações.'},
        {'chave': 'contacto', 'titulo': 'Email ou telefone da loja', 'seccao': 'configuracoes',
         'ok': bool((loja.contacto_email or '').strip() or (loja.contacto_telefone or '').strip()),
         'ajuda': 'Em Configurações → Contactos da loja.'},
        {'chave': 'devolucoes', 'titulo': 'Política de devoluções', 'seccao': 'configuracoes',
         'ok': bool((loja.politica_devolucao or '').strip()),
         'ajuda': 'Em Configurações → Políticas.'},
        {'chave': 'entregas', 'titulo': 'Política de entregas', 'seccao': 'configuracoes',
         'ok': bool((loja.politica_entregas or '').strip()) or not entrega,
         'ajuda': 'Em Configurações → Políticas (só conta se fizeres entregas ao domicílio).'},
        {'chave': 'produto', 'titulo': 'Pelo menos 1 produto ou serviço completo', 'seccao': 'produtos',
         'ok': bool(completos or servicos_ok),
         'ajuda': f'Com foto, preço e descrição (pelo menos {DESCRICAO_MIN} caracteres).'},
    ]
    # com pagamentos online a sério, quem aceita cartão (ou tem serviços pagos antecipadamente) precisa do seu
    # contrato vinti4 ativo — a SISP paga direto à loja (utils/vinti4.py). Sem ele, o online fica suspenso (utils/banco).
    from ..pagamentos import cobra_a_serio
    from ..pagamentos.servico import METODOS_ONLINE
    if cobra_a_serio() and (loja.metodos_pagamento.filter(ativo=True, tipo__in=METODOS_ONLINE).exists()
                            or (cfg and cfg.ativo and loja.servicos.filter(ativo=True, pagamento__in=('antecipado', 'ambos')).exists())):
        from .vinti4 import ativa
        requisitos.append({'chave': 'vinti4', 'titulo': 'Contrato vinti4 ativo (pagamento com cartão)', 'seccao': 'configuracoes',
                           'ok': ativa(loja),
                           'ajuda': 'Em Configurações → Pagamento com cartão (só o dono): a adesão da loja à SISP. Até lá, '
                                    'o cartão não aparece aos clientes e as marcações não se pagam antecipadamente — '
                                    'ou desliga o cartão e vende com dinheiro/transferência.'})
    # transferência ligada: o cliente precisa do IBAN da loja (utils/banco.dados_transferencia)
    if loja.metodos_pagamento.filter(ativo=True, tipo='transferencia').exists():
        from .banco import tem_dados
        requisitos.append({'chave': 'banco', 'titulo': 'Dados bancários (para receber transferências)', 'seccao': 'configuracoes',
                           'ok': tem_dados(loja),
                           'ajuda': 'Em Configurações → Dados bancários (só o dono). Sem eles a transferência não aparece aos '
                                    'clientes — ou desliga a transferência.'})
    # documentos legais: opcionais, a não ser que o admin os peça a esta loja (utils/documentos_loja.py)
    if loja.documentos_obrigatorios:
        from .documentos_loja import verificada
        requisitos.append({'chave': 'documentos', 'titulo': 'Loja verificada (documentos aprovados)',
                           'seccao': 'configuracoes', 'ok': verificada(loja),
                           'ajuda': 'Em Configurações → Documentos (só o dono): documento de identificação e início de '
                                    'atividade ou certidão comercial, aprovados pela Bende.'})
    feitos = sum(r['ok'] for r in requisitos)
    out = {
        'percentagem': round(100 * feitos / len(requisitos)),
        'completa': feitos == len(requisitos),
        'requisitos': requisitos,
        'produtos_completos': completos,
        'produtos_incompletos_total': incompletos,
    }
    if com_produtos:
        out['produtos_incompletos'] = lista
    return out


def faltam_titulos(loja):
    """Títulos dos requisitos em falta (mensagens do admin)."""
    return [r['titulo'] for r in avaliar(loja)['requisitos'] if not r['ok']]
