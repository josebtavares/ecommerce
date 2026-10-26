"""
Exportação dos dados de uma loja: um ZIP com CSV legíveis (abrem no Excel) — não serve para repor.

  pedir(loja, user, com_imagens, pelo_admin) → ExportacaoLoja na fila (ou ExportacaoEmCurso / LimiteExportacoes)
  processar_fila()                           → o worker (manage.py processar_videos) gera a próxima da fila
  expirar()                                  → apaga os ficheiros com mais de DIAS_VALIDADE dias

O ZIP é montado num ficheiro temporário (pode ter centenas de MB com imagens) e vai para o
armazenamento privado dos backups (utils/backups.armazenamento): tem dados pessoais dos clientes.
Descarrega-se por link temporário (Views/exportacaoLojaView.py).
"""
import json
import logging
import re
import shutil
import tempfile
import zipfile
from datetime import timedelta
from pathlib import Path

from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Count, Max, Min, Sum
from django.utils import timezone

from ..models import (AvaliacaoLoja, Encomenda, ExportacaoLoja, HorarioLoja, ExcecaoHorario, ItemEncomenda,
                      OpcaoEntrega, Produto, Reembolso, UtilizadorLoja, VarianteProduto)
from . import backups

log = logging.getLogger(__name__)

DIAS_VALIDADE = 7
MAX_POR_DIA = 5                       # por loja
LIMITE_MEDIA = 2 * 1024 ** 3          # imagens/vídeos: acima disto o resto fica de fora (e diz-se no LEIA-ME)
ENCRAVADA = timedelta(hours=2)


class ExportacaoEmCurso(Exception):
    pass


class LimiteExportacoes(Exception):
    pass


# ── pedir ──────────────────────────────────────────────────────────

def pedir(loja, user, com_imagens=False, pelo_admin=False):
    with transaction.atomic():
        ativas = ExportacaoLoja.objects.select_for_update().filter(loja=loja, estado__in=('pendente', 'a_correr'))
        if ativas.exists():
            raise ExportacaoEmCurso('Já há uma exportação desta loja a ser preparada.')
        hoje = ExportacaoLoja.objects.filter(loja=loja, criado_em__gte=timezone.now() - timedelta(days=1)).count()
        if hoje >= MAX_POR_DIA:
            raise LimiteExportacoes(f'Esta loja já fez {MAX_POR_DIA} exportações nas últimas 24 horas.')
        return ExportacaoLoja.objects.create(loja=loja, pedido_por=user, com_imagens=bool(com_imagens),
                                             pelo_admin=pelo_admin)


# ── worker ─────────────────────────────────────────────────────────

def processar_fila():
    """Gera uma exportação da fila (a mais antiga). Devolve True se gerou alguma."""
    ExportacaoLoja.objects.filter(estado='a_correr', iniciado_em__lt=timezone.now() - ENCRAVADA).update(
        estado='erro', erro='Interrompida (o processo parou a meio).')
    with transaction.atomic():
        exp = (ExportacaoLoja.objects.select_for_update(skip_locked=True)
               .filter(estado='pendente').order_by('criado_em').first())
        if not exp:
            return False
        exp.estado, exp.iniciado_em = 'a_correr', timezone.now()
        exp.save(update_fields=['estado', 'iniciado_em'])
    gerar(exp)
    return True


def expirar(agora=None):
    agora = agora or timezone.now()
    n = 0
    arm = backups.armazenamento()
    for exp in ExportacaoLoja.objects.filter(estado='ok', expira_em__lt=agora):
        try:
            if exp.chave:
                arm.apagar(exp.chave)
            exp.estado = 'expirada'
            exp.save(update_fields=['estado'])
            n += 1
        except Exception:
            log.exception('exportação: não consegui apagar %s', exp.chave)
    return n


def gerar(exp):
    pasta = tempfile.mkdtemp(prefix='exportacao-')
    try:
        loja = exp.loja
        local = timezone.localtime(exp.iniciado_em or timezone.now())
        nome = f'bende-loja-{loja.id}-{_slug(loja.nome)}-{local:%Y%m%d-%H%M%S}.zip'
        ficheiro = Path(pasta) / nome
        avisos = escrever_zip(ficheiro, exp)
        chave = f'exportacoes/loja-{loja.id}/{nome}'
        backups.armazenamento().guardar(ficheiro, chave)
        exp.chave, exp.tamanho, exp.estado = chave, ficheiro.stat().st_size, 'ok'
        exp.avisos = '\n'.join(avisos)[:20000]
        exp.expira_em = timezone.now() + timedelta(days=DIAS_VALIDADE)
    except Exception as e:
        log.exception('exportação da loja %s falhou', exp.loja_id)
        exp.estado, exp.erro = 'erro', str(e)[:4000]
    finally:
        shutil.rmtree(pasta, ignore_errors=True)
        exp.concluido_em = timezone.now()
        exp.save(update_fields=['chave', 'tamanho', 'estado', 'avisos', 'expira_em', 'erro', 'concluido_em'])
    _avisar(exp)
    return exp


def _avisar(exp):
    """Notificação a quem pediu (no backoffice ou no admin)."""
    from ..Views.notificacaoView import notificar
    u = getattr(exp.pedido_por, 'utilizador', None) if exp.pedido_por else None
    if not u:
        return
    link = '/admin?seccao=lojas' if exp.pelo_admin else f'/loja/{exp.loja_id}/backoffice?seccao=configuracoes'
    ok = exp.estado == 'ok'
    try:
        notificar(u, 'exportacao_pronta',
                  f'Exportação de «{exp.loja.nome}» ' + ('pronta' if ok else 'falhou'),
                  (f'O ficheiro fica disponível {DIAS_VALIDADE} dias.' if ok else 'Tenta outra vez; se voltar a falhar, fala com o suporte.'),
                  loja=exp.loja, link=link)
    except Exception:
        log.exception('exportação: não consegui notificar')


# ── o ZIP ──────────────────────────────────────────────────────────

def _slug(texto):
    return re.sub(r'[^\w-]+', '-', (texto or '').lower()).strip('-')[:40] or 'loja'


def _v(x):
    return '' if x is None else f'{x:.2f}'.replace('.', ',')


def _pessoa(u):
    """(nome, email, telefone) de um Utilizador."""
    if not u:
        return '', '', ''
    return (u.user.get_full_name() or u.user.username), u.user.email, u.telefone


def escrever_zip(destino, exp):
    from ..Views.faturacaoView import _csv, _quando, escrever_arquivo
    loja = exp.loja
    avisos = []

    with zipfile.ZipFile(destino, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        def csv(nome, cabecalho, linhas):
            zf.writestr(nome, _csv([cabecalho] + list(linhas)))

        # loja
        dados = {
            'id': loja.id, 'nome': loja.nome, 'descricao': loja.descricao, 'categoria': loja.categoria,
            'localizacao': loja.localizacao, 'estado': loja.get_estado_display(),
            'criada_em': _quando(loja.data_criacao), 'dono': dict(zip(('nome', 'email', 'telefone'), _pessoa(loja.dono))),
            'nif': getattr(loja, 'nif', ''), 'percentagem_iva': str(loja.percentagem_iva),
            'modelo_cobranca': loja.get_modelo_cobranca_display(), 'percentagem_comissao': str(loja.percentagem_comissao),
            'entrega_ativa': loja.entrega_ativa, 'levantamento_ativo': loja.levantamento_ativo,
            'politica_devolucao': loja.politica_devolucao, 'termos_servico': loja.termos_servico,
            'politica_privacidade': loja.politica_privacidade,
            'aspeto': {'template': loja.template_id, 'cor_primaria': loja.cor_primaria, 'cor_secundaria': loja.cor_secundaria,
                       'modo_escuro': loja.dark_mode},
            'horario': [{'dia': h.get_dia_semana_display(), 'abre': f'{h.abre:%H:%M}', 'fecha': f'{h.fecha:%H:%M}'}
                        for h in HorarioLoja.objects.filter(loja=loja).order_by('dia_semana', 'abre')],
            'excecoes_horario': [{'de': str(e.inicio), 'ate': str(e.fim), 'intervalos': e.intervalos, 'mensagem': e.mensagem}
                                 for e in ExcecaoHorario.objects.filter(loja=loja).order_by('inicio')],
            'opcoes_entrega': [{'nome': o.nome, 'preco': _v(o.preco), 'tempo': o.tempo_estimado, 'area': o.area_cobertura,
                                'ativa': o.ativa} for o in OpcaoEntrega.objects.filter(loja=loja)],
            'categorias': [{'nome': c.nome, 'ativa': c.ativo} for c in loja.categorias.order_by('ordem', 'nome')],
        }
        zf.writestr('loja.json', json.dumps(dados, ensure_ascii=False, indent=2))

        csv('equipa.csv', ['Nome', 'Email', 'Telefone', 'Função', 'Ativo', 'Desde'],
            [[*_pessoa(m.utilizador), m.get_role_display(), 'sim' if m.ativo else 'não', _quando(m.data_entrada)]
             for m in UtilizadorLoja.objects.filter(loja=loja).select_related('utilizador__user')])

        # catálogo
        produtos = (Produto.objects.filter(loja=loja).select_related('tipo', 'inventario')
                    .prefetch_related('categorias', 'componentes__produto', 'componentes__variante').order_by('id'))
        linhas = []
        for p in produtos:
            inv = getattr(p, 'inventario', None)
            linhas.append([p.id, p.nome, p.sku, getattr(p.tipo, 'nome', ''), ', '.join(c.nome for c in p.categorias.all()),
                           _v(p.preco), _v(inv.preco_custo) if inv else '',
                           'por variante' if p.stock_por_variante else (inv.quantidade if inv else ''),
                           'sim' if p.ativo else 'não', 'sim' if p.destaque else 'não', 'sim' if p.disponivel_pos else 'não',
                           ' + '.join(f'{c.quantidade}× {c.produto.nome}' + (f' ({c.variante.descricao()})' if c.variante_id else '')
                                      for c in p.componentes.all()) if p.e_conjunto else '',
                           json.dumps(p.atributos, ensure_ascii=False) if p.atributos else '', p.descricao, _quando(p.data_criacao)])
        csv('produtos.csv', ['ID', 'Nome', 'SKU', 'Tipo', 'Categorias', 'Preço (CVE)', 'Custo (CVE)', 'Stock', 'Ativo',
                             'Destaque', 'No POS', 'Conjunto (componentes)', 'Atributos', 'Descrição', 'Criado em'], linhas)
        csv('variantes.csv', ['ID', 'Produto ID', 'Produto', 'Variante', 'SKU', 'Preço (CVE)', 'Stock', 'Ativa'],
            [[v.id, v.produto_id, v.produto.nome, v.descricao(), v.sku, _v(v.preco_efetivo), v.quantidade,
              'sim' if v.ativo else 'não']
             for v in VarianteProduto.objects.filter(produto__loja=loja).select_related('produto').order_by('produto_id', 'id')])

        # vendas online
        encomendas = (Encomenda.objects.filter(loja=loja).select_related('comprador__user', 'opcao_entrega', 'pagamento')
                      .order_by('data_criacao'))
        linhas = []
        for e in encomendas:
            pag = getattr(e, 'pagamento', None)
            linhas.append([f'E-{e.id}', _quando(e.data_criacao), e.get_status_display(), *_pessoa(e.comprador),
                           e.get_tipo_entrega_display(), getattr(e.opcao_entrega, 'nome', ''), e.morada_entrega,
                           _v(e.valor_total), pag.get_status_display() if pag else '', _quando(pag.data_pagamento) if pag else '',
                           e.fatura_numero, _quando(e.data_conclusao), e.notas])
        csv('encomendas.csv', ['Encomenda', 'Data', 'Estado', 'Cliente', 'Email', 'Telefone', 'Entrega', 'Opção de entrega',
                               'Morada', 'Total (CVE)', 'Pagamento', 'Pago em', 'Fatura nº', 'Concluída em', 'Notas'], linhas)
        csv('encomendas-itens.csv', ['Encomenda', 'Produto ID', 'Produto', 'Variante / opções', 'Quantidade',
                                     'Preço unitário (CVE)', 'Total (CVE)', 'Custo unitário (CVE)'],
            [[f'E-{i.encomenda_id}', i.produto_id or '', getattr(i.produto, 'nome', '(produto apagado)'),
              i.variante.descricao() if i.variante_id else (json.dumps(i.atributos, ensure_ascii=False) if i.atributos else ''),
              i.quantidade, _v(i.preco), _v(i.preco * i.quantidade), _v(i.custo_unitario)]
             for i in ItemEncomenda.objects.filter(encomenda__loja=loja).select_related('produto', 'variante')
                                           .order_by('encomenda_id', 'id')])

        csv('devolucoes.csv', ['Pedido', 'Encomenda', 'Data', 'Cliente', 'Email', 'Tipo', 'Motivo', 'Estado',
                               'Valor pedido (CVE)', 'Valor aprovado (CVE)', 'Método', 'Reembolsado em', 'Descrição'],
            [[r.id, f'E-{r.encomenda_id}', _quando(r.data_criacao), *_pessoa(r.comprador)[:2], r.get_tipo_display(),
              r.get_motivo_display(), r.get_estado_display(), _v(r.valor_pedido), _v(r.valor_aprovado),
              r.get_metodo_display() if r.metodo else '', _quando(r.data_reembolso), r.descricao]
             for r in Reembolso.objects.filter(loja=loja).select_related('comprador__user').order_by('data_criacao')])

        csv('avaliacoes.csv', ['Data', 'Cliente', 'Encomenda', 'Pontuação', 'Comentário', 'Oculta'],
            [[_quando(a.data_criacao), _pessoa(a.utilizador)[0], f'E-{a.encomenda_id}' if a.encomenda_id else '',
              a.pontuacao, a.comentario, 'sim' if a.oculta else 'não']
             for a in AvaliacaoLoja.objects.filter(loja=loja).select_related('utilizador__user').order_by('data_criacao')])

        # serviços e marcações
        from ..servicos.models import Marcacao, Profissional, Servico
        servicos = Servico.objects.filter(loja=loja).prefetch_related('profissionais').order_by('ordem', 'id')
        if servicos.exists() or Marcacao.objects.filter(loja=loja).exists():
            csv('servicos.csv', ['ID', 'Nome', 'Categoria', 'Duração (min)', 'Intervalo (min)', 'Preço (CVE)', 'Tipo de preço',
                                 'Pagamento', 'Pacote', 'Ativo', 'Visível', 'Profissionais', 'Descrição'],
                [[s.id, s.nome, s.categoria, s.duracao_min, s.intervalo_min, _v(s.preco), s.get_tipo_preco_display(),
                  s.get_pagamento_display(), 'sim' if s.e_pacote else 'não', 'sim' if s.ativo else 'não',
                  'sim' if s.visivel else 'não', ', '.join(p.nome for p in s.profissionais.all()), s.descricao]
                 for s in servicos])
            csv('profissionais.csv', ['ID', 'Nome', 'Descrição', 'Ativo'],
                [[p.id, p.nome, p.descricao, 'sim' if p.ativo else 'não']
                 for p in Profissional.objects.filter(loja=loja).order_by('ordem', 'id')])
            linhas = []
            for m in (Marcacao.objects.filter(loja=loja).select_related('cliente__user', 'profissional')
                      .order_by('inicio')):
                nome, email, tel = _pessoa(m.cliente) if m.cliente_id else (m.cliente_nome, '', m.cliente_telefone)
                linhas.append([f'M-{m.id}', _quando(m.inicio), _quando(m.fim, '%H:%M'), m.servico_nome, m.profissional.nome,
                               nome, email, tel, m.get_estado_display(), _v(m.preco_indicado), _v(m.preco_final),
                               m.get_pagamento_display(), 'sim' if m.pago else 'não', _v(m.valor_pago), m.criada_por,
                               m.cancelada_motivo, m.notas_cliente])
            csv('marcacoes.csv', ['Marcação', 'Início', 'Fim', 'Serviço', 'Profissional', 'Cliente', 'Email', 'Telefone',
                                  'Estado', 'Preço indicado (CVE)', 'Preço final (CVE)', 'Pagamento', 'Pago',
                                  'Valor pago (CVE)', 'Criada por', 'Motivo do cancelamento', 'Notas do cliente'], linhas)

        # POS ligados à loja
        from ..pos.models import ContaMesa, ItemContaMesa, TurnoPOS
        contas = ContaMesa.objects.filter(loja=loja).select_related('pos', 'mesa').order_by('criada_em')
        if contas.exists():
            csv('pos/contas.csv', ['Conta', 'POS', 'Mesa', 'Aberta em', 'Fechada em', 'Estado', 'Atendente',
                                   'Subtotal (CVE)', 'Taxa de serviço (CVE)', 'Desconto (CVE)', 'Motivo do desconto',
                                   'Gorjeta (CVE)', 'Total (CVE)', 'Pagamento', 'NIF do cliente', 'Fatura nº'],
                [[f'V-{c.id}', c.pos.nome, c.mesa.numero if c.mesa_id else '',
                  _quando(c.criada_em), _quando(c.fechada_em), c.get_status_display(), c.atendente_nome,
                  _v(c.subtotal), _v(c.taxa_servico_valor), _v(c.desconto_valor), c.desconto_motivo, _v(c.gorjeta),
                  _v(c.total), c.get_metodo_pagamento_display() if c.metodo_pagamento else '', c.nif_cliente, c.fatura_numero]
                 for c in contas])
            csv('pos/contas-itens.csv', ['Conta', 'Produto', 'Quantidade', 'Preço unitário (CVE)', 'Total (CVE)'],
                [[f'V-{i.conta_id}', i.nome, i.quantidade, _v(i.preco_unitario), _v(i.preco_total)]
                 for i in ItemContaMesa.objects.filter(conta__loja=loja).order_by('conta_id', 'id')])
        turnos = TurnoPOS.objects.filter(pos__loja_vinculada=loja).select_related('pos').order_by('aberto_em')
        if turnos.exists():
            csv('pos/turnos.csv', ['POS', 'Operador', 'Aberto em', 'Fechado em', 'Fechado por', 'Abertura (CVE)',
                                   'Fecho (CVE)', 'Diferença (CVE)', 'Observações'],
                [[t.pos.nome, t.operador_nome, _quando(t.aberto_em), _quando(t.fechado_em), t.fechado_por,
                  _v(t.valor_abertura), _v(t.valor_fecho), _v(t.diferenca), t.observacoes] for t in turnos])

        # clientes (quem comprou ou marcou nesta loja)
        clientes = {}
        # .order_by() vazio: a ordenação por data entrava no GROUP BY e partia cada cliente em várias linhas
        for c in (encomendas.exclude(status__in=('pendente', 'cancelado')).order_by().values('comprador')
                  .annotate(n=Count('id'), total=Sum('valor_total'), primeira=Min('data_criacao'), ultima=Max('data_criacao'))):
            clientes[c['comprador']] = {'enc': c['n'], 'total': c['total'], 'primeira': c['primeira'], 'ultima': c['ultima'],
                                        'marc': 0}
        for c in (Marcacao.objects.filter(loja=loja, cliente__isnull=False).exclude(estado__in=('cancelada', 'expirada'))
                  .order_by().values('cliente').annotate(n=Count('id'), primeira=Min('inicio'), ultima=Max('inicio'))):
            d = clientes.setdefault(c['cliente'], {'enc': 0, 'total': 0, 'primeira': c['primeira'], 'ultima': c['ultima'], 'marc': 0})
            d['marc'] = c['n']
            d['primeira'], d['ultima'] = min(d['primeira'], c['primeira']), max(d['ultima'], c['ultima'])
        from ..models import Utilizador
        pessoas = {u.id: u for u in Utilizador.objects.filter(id__in=clientes).select_related('user')}
        csv('clientes.csv', ['Nome', 'Email', 'Telefone', 'Encomendas', 'Total gasto (CVE)', 'Marcações',
                             'Primeira vez', 'Última vez'],
            sorted(([*_pessoa(pessoas.get(uid)), d['enc'], _v(d['total'] or 0), d['marc'], _quando(d['primeira']),
                     _quando(d['ultima'])] for uid, d in clientes.items()), key=lambda l: (l[0] or '').lower()))

        # faturação (o mesmo conteúdo do arquivo fiscal do separador Faturação, desde sempre)
        try:
            avisos += [f'faturacao/{f}' for f in escrever_arquivo(zf, loja, 'loja', None, None, prefixo='faturacao/')]
        except Exception as e:
            log.exception('exportação: arquivo fiscal da loja %s', loja.id)
            avisos.append(f'faturacao/: não foi possível juntar o arquivo fiscal ({e})')

        # imagens e vídeos
        n_media = 0
        if exp.com_imagens:
            n_media, cortadas = _juntar_media(zf, loja, avisos)
            if cortadas:
                avisos.append(f'imagens/: {cortadas} ficheiro(s) ficaram de fora — o ZIP passava de '
                              f'{LIMITE_MEDIA // 1024 ** 3} GB. Os restantes podem ser descarregados na loja.')

        leia = [
            f'Dados da loja «{loja.nome}» (id {loja.id}) — exportados pelo Bende a {_quando(timezone.now())}.',
            'Ficheiros CSV separados por ; (abrem no Excel). Valores em escudos (CVE). Datas na hora de Cabo Verde.',
            'Este ZIP serve para consultar e guardar os teus dados; não se importa de volta para o Bende.', '',
            'loja.json                 dados da loja, horário, opções de entrega, categorias e políticas',
            'equipa.csv                quem tem acesso ao backoffice e com que função',
            'produtos.csv              catálogo (preço, custo, stock, conjuntos); variantes.csv as variantes com o stock',
            'encomendas.csv            vendas online; encomendas-itens.csv os artigos de cada uma',
            'devolucoes.csv            pedidos de devolução / reembolso',
            'avaliacoes.csv            avaliações dos clientes',
            'clientes.csv              quem comprou ou marcou na loja (contacto, nº de compras, total)',
            'servicos.csv, profissionais.csv, marcacoes.csv   serviços e marcações (se a loja os tiver)',
            'pos/                      contas, artigos e turnos de caixa dos POS ligados à loja (se houver)',
            'faturacao/                arquivo fiscal: faturas, comprovativos e documentos do Bende (tem o seu LEIA-ME)',
            f'imagens/                  logótipo, banner e imagens dos produtos e serviços ({n_media} ficheiros)'
            if exp.com_imagens else 'imagens/                  (não incluídas — escolhe «com imagens» ao exportar)',
            '', 'Atenção: clientes.csv, encomendas.csv e marcacoes.csv têm dados pessoais. Guarda o ficheiro em lugar seguro.',
        ]
        if avisos:
            leia += ['', 'Avisos:'] + avisos
        zf.writestr('LEIA-ME.txt', '\r\n'.join(leia))
    return avisos


def _juntar_media(zf, loja, avisos):
    from ..servicos.models import Profissional, ServicoImagem
    from ..models import ProdutoImagem
    ficheiros = []                                  # (caminho no ZIP, nome no armazenamento)

    def junta(pasta, campo, nome):
        if campo and getattr(campo, 'name', ''):
            ext = Path(campo.name).suffix.lower()
            ficheiros.append((f'imagens/{pasta}/{nome}{ext}', campo.name))

    junta('loja', loja.logo, 'logo')
    junta('loja', loja.banner, 'banner')
    for p in Produto.objects.filter(loja=loja).prefetch_related('imagens').order_by('id'):
        pasta = f'produtos/{p.id}-{_slug(p.nome)}'
        junta(pasta, p.ficheiro, 'principal')
        for i, img in enumerate(p.imagens.all(), 1):
            junta(pasta, img.ficheiro, f'{i:02d}')
    for img in ServicoImagem.objects.filter(servico__loja=loja).select_related('servico').order_by('servico_id', 'ordem', 'id'):
        junta(f'servicos/{img.servico_id}-{_slug(img.servico.nome)}', img.ficheiro, f'{img.id}')
    for p in Profissional.objects.filter(loja=loja):
        junta('profissionais', p.foto, f'{p.id}-{_slug(p.nome)}')

    total = n = cortadas = 0
    for caminho, nome in ficheiros:
        try:
            tamanho = default_storage.size(nome)
        except Exception:
            avisos.append(f'{caminho} (não encontrado no armazenamento)')
            continue
        if total + tamanho > LIMITE_MEDIA:
            cortadas += 1
            continue
        try:
            info = zipfile.ZipInfo(caminho, timezone.localtime().timetuple()[:6])
            info.compress_type = zipfile.ZIP_STORED     # imagens e vídeos já vêm comprimidos
            with default_storage.open(nome, 'rb') as origem, zf.open(info, 'w', force_zip64=True) as dest:
                shutil.copyfileobj(origem, dest, 1024 * 1024)
            total += tamanho
            n += 1
        except Exception:
            avisos.append(f'{caminho} (não foi possível ler)')
    return n, cortadas
