"""
Ficheiro de reconciliação VBVT da SISP (MOP021 v14, secção 3; Plan Test 36–37).

A SISP gera-o todos os dias no fecho da rede vinti4, com todas as transacções do comerciante; descarrega-se do
Portal do Comerciante e carrega-se em Admin → Pagamentos → Cartão → Reconciliação. Registos de largura fixa:

  0 header   tipo(1) VBVT(4) versão(2) merchantID(15) data(8) seq(3) data anterior(8) seq anterior(3) moeda(3)
  1 compra   tipo(1) merchantRef(20) messageID(20) rt(1) quando(14) período(4) tid(8) pan(16) valor(13) comissão(13) cartão(5)
  2 estorno  tipo(1) merchantRef(20) messageID(20) rt(1) quando(14) período(4) tid(8) valor(13) pan(16)
             ref original(20) período original(4) tid original(8) comissão(13) cartão(5)
  3 serviço  (pagamento de serviço / recarga — a Bendi não usa: só se conta)
  9 trailer  tipo(1) nº de registos de detalhe(8)

N = números com zeros à esquerda, A = texto com espaços à direita, N13:2 = valor com 2 casas sem ponto.

Processar = validar tudo primeiro (estrutura, Merchant ID, sequência); com algum erro o ficheiro fica "rejeitado" e
nada muda. Aplicado: cada compra/estorno é comparado com a TransacaoVinti4 do mesmo merchantRef. O ficheiro nunca
dá nada como pago — uma compra aprovada lá e não cá fica assinalada, e confirma-se com "Perguntar à SISP"
(API de estado), que é quem aplica o pagamento.
"""
import hashlib
from datetime import date, datetime
from decimal import Decimal

from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone

TAMANHO_MAX = 5 * 1024 * 1024
MAX_LINHAS_GUARDADAS = 5000

# (nome, início, tamanho, tipo)  tipo: n = número, a = texto, v = valor N13:2, t = AAAAMMDDhhmmss, d = AAAAMMDD
_CAMPOS = {
    '0': [('tipo_ficheiro', 1, 4, 'a'), ('versao', 5, 2, 'n'), ('merchant_id', 7, 15, 'n'), ('data', 22, 8, 'd'),
          ('sequencia', 30, 3, 'n'), ('data_anterior', 33, 8, 'd'), ('sequencia_anterior', 41, 3, 'n'),
          ('moeda', 44, 3, 'n')],
    '1': [('ref', 1, 20, 'a'), ('message_id', 21, 20, 'a'), ('rt', 41, 1, 'a'), ('quando', 42, 14, 't'),
          ('periodo', 56, 4, 'n'), ('tid', 60, 8, 'n'), ('pan', 68, 16, 'a'), ('valor', 84, 13, 'v'),
          ('comissao', 97, 13, 'v'), ('cartao', 110, 5, 'a')],
    '2': [('ref', 1, 20, 'a'), ('message_id', 21, 20, 'a'), ('rt', 41, 1, 'a'), ('quando', 42, 14, 't'),
          ('periodo', 56, 4, 'n'), ('tid', 60, 8, 'n'), ('valor', 68, 13, 'v'), ('pan', 81, 16, 'a'),
          ('ref_original', 97, 20, 'a'), ('periodo_original', 117, 4, 'n'), ('tid_original', 121, 8, 'n'),
          ('comissao', 129, 13, 'v'), ('cartao', 142, 5, 'a')],
    '3': [('ref', 1, 20, 'a'), ('message_id', 21, 20, 'a'), ('rt', 41, 1, 'a'), ('quando', 42, 14, 't'),
          ('periodo', 56, 4, 'n'), ('tid', 60, 8, 'n'), ('pan', 68, 16, 'a'), ('valor', 84, 13, 'v'),
          ('comissao', 97, 13, 'v'), ('entidade', 110, 5, 'n'), ('referencia_servico', 115, 9, 'n')],
    '9': [('registos', 1, 8, 'n')],
}
# campos que podem vir em branco (o cartão "vazio" quer dizer tipo não identificado; um estorno com erro não tem
# a transacção original)
_OPCIONAIS = {'cartao', 'pan', 'message_id', 'ref_original', 'periodo_original', 'tid_original', 'data_anterior',
              'sequencia_anterior', 'comissao'}

TIPOS_REGISTO = {'1': 'compra', '2': 'estorno', '3': 'servico'}
RESULTADOS = {
    'ok':               'Confere',
    'recusada':         'Recusada (igual cá)',
    'valor_diferente':  'Valor diferente do nosso',
    'paga_so_na_sisp':  'Aprovada na SISP, não paga cá — perguntar à SISP',
    'paga_so_ca':       'Paga cá, recusada na SISP — verificar',
    'estorno':          'Estorno feito',
    'estorno_recusado': 'Estorno recusado',
    'desconhecida':     'Não é nossa (merchantRef desconhecido)',
    'nao_aplicavel':    'Pagamento de serviço/recarga (não usado)',
}
PROBLEMAS = ('valor_diferente', 'paga_so_na_sisp', 'paga_so_ca', 'desconhecida')


class ErroVBVT(Exception):
    pass


def _so_digitos(v):
    return v.isdigit()


def _ler_campo(linha, ini, tam, tipo, nome):
    bruto = linha[ini:ini + tam]
    v = bruto.strip()
    if tipo in ('d', 't') and v and set(v) == {'0'}:     # o primeiro ficheiro não tem anterior: vem a zeros
        v = ''
    if not v:
        if nome in _OPCIONAIS:
            return '' if tipo == 'a' else None
        raise ErroVBVT(f'{nome} em branco')
    if tipo == 'a':
        return v
    if not _so_digitos(v):
        raise ErroVBVT(f'{nome} devia ser numérico ("{v[:20]}")')
    if tipo == 'n':
        return int(v)
    if tipo == 'v':
        return Decimal(int(v)).scaleb(-2)          # N13:2 → 2 casas: '0000000150000' = 1500.00
    try:
        if tipo == 'd':
            return datetime.strptime(v, '%Y%m%d').date()
        return datetime.strptime(v, '%Y%m%d%H%M%S')
    except ValueError:
        raise ErroVBVT(f'{nome} não é uma data válida ("{v}")')


def _tamanho(tipo):
    ini, tam = _CAMPOS[tipo][-1][1:3]
    return ini + tam


def _texto(conteudo):
    for enc in ('utf-8-sig', 'cp1252', 'latin-1'):
        try:
            return conteudo.decode(enc)
        except UnicodeDecodeError:
            continue
    return conteudo.decode('latin-1', errors='replace')


def ler(conteudo):
    """bytes → {'header', 'detalhes': [(nº linha, tipo, campos)], 'trailer', 'erros': [{linha, erro}]}.
    Lê tudo o que conseguir para mostrar todos os erros de uma vez."""
    erros, detalhes, header, trailer = [], [], None, None
    n_detalhe = 0                       # registos 1/2/3 no ficheiro, válidos ou não (para comparar com o trailer)
    linhas = [(i, l.rstrip('\r\n')) for i, l in enumerate(_texto(conteudo).split('\n'), 1)]
    linhas = [(i, l) for i, l in linhas if l.strip()]
    if not linhas:
        return {'header': None, 'detalhes': [], 'trailer': None, 'erros': [{'linha': 0, 'erro': 'O ficheiro está vazio.'}]}
    for pos, (n, linha) in enumerate(linhas):
        tipo = linha[:1]
        if tipo not in _CAMPOS:
            erros.append({'linha': n, 'erro': f'Tipo de registo desconhecido ("{tipo}").'})
            continue
        if tipo == '0' and pos != 0:
            erros.append({'linha': n, 'erro': 'Header fora da primeira linha.'})
            continue
        if pos == 0 and tipo != '0':
            erros.append({'linha': n, 'erro': 'A primeira linha tem de ser o header (registo 0).'})
        if trailer is not None:
            erros.append({'linha': n, 'erro': 'Registo depois do trailer.'})
            continue
        if tipo in TIPOS_REGISTO:
            n_detalhe += 1
        if len(linha.rstrip()) > _tamanho(tipo):
            erros.append({'linha': n, 'erro': f'Linha maior do que o registo {tipo} ({len(linha.rstrip())} > {_tamanho(tipo)}).'})
            continue
        linha = linha.ljust(_tamanho(tipo))
        try:
            campos = {nome: _ler_campo(linha, ini, tam, t, nome) for nome, ini, tam, t in _CAMPOS[tipo]}
        except ErroVBVT as e:
            erros.append({'linha': n, 'erro': f'Registo {tipo}: {e}.'})
            continue
        if tipo == '0':
            if campos['tipo_ficheiro'] != 'VBVT':
                erros.append({'linha': n, 'erro': f'Tipo de ficheiro "{campos["tipo_ficheiro"]}" (esperado VBVT).'})
            if campos['versao'] != 1:
                erros.append({'linha': n, 'erro': f'Versão {campos["versao"]:02d} (esperada 01).'})
            if campos['moeda'] != 132:
                erros.append({'linha': n, 'erro': f'Moeda {campos["moeda"]} (esperada 132, escudos).'})
            if campos['sequencia'] < 1:
                erros.append({'linha': n, 'erro': 'A sequência começa em 001.'})
            header = campos
        elif tipo == '9':
            trailer = campos
        else:
            if campos['rt'] not in ('0', '2'):
                erros.append({'linha': n, 'erro': f'RT Response Code "{campos["rt"]}" (esperado 0 ou 2).'})
                continue
            detalhes.append((n, tipo, campos))
    if trailer is None:
        erros.append({'linha': linhas[-1][0], 'erro': 'Falta o trailer (registo 9): o ficheiro pode estar incompleto.'})
    elif trailer['registos'] != n_detalhe:
        erros.append({'linha': linhas[-1][0], 'erro': f'O trailer diz {trailer["registos"]} registos de detalhe e o '
                                                      f'ficheiro tem {n_detalhe}.'})
    return {'header': header, 'detalhes': detalhes, 'trailer': trailer, 'erros': erros}


# ── dono do ficheiro e sequência ───────────────────────────────

def _normalizar_mid(v):
    v = ''.join(str(v or '').split())
    return v.lstrip('0') or ('0' if v else '')


def dono(merchant_id):
    """Merchant ID → ('bendi', None) | ('loja', loja) | None. A Bendi e uma loja podem partilhar o contrato
    (CV PRIME STORE): conta como da Bendi."""
    from ..models import AdesaoVinti4
    mid = _normalizar_mid(merchant_id)
    if not mid:
        return None
    if mid == _normalizar_mid(settings.VINTI4_MERCHANT_ID):
        return 'bendi', None
    for a in AdesaoVinti4.objects.select_related('loja').exclude(merchant_id=''):
        if _normalizar_mid(a.merchant_id) == mid:
            return 'loja', a.loja
    return None


def lojas_do_mid(mid):
    """Ids das lojas cujo contrato vinti4 tem este Merchant ID (a loja da CV PRIME partilha o da Bendi)."""
    from ..models import AdesaoVinti4
    mid = _normalizar_mid(mid)
    return [a.loja_id for a in AdesaoVinti4.objects.exclude(merchant_id='').only('loja_id', 'merchant_id')
            if mid and _normalizar_mid(a.merchant_id) == mid]


def mid_da_loja(loja):
    from ..models import AdesaoVinti4
    a = AdesaoVinti4.objects.filter(loja=loja).only('merchant_id').first()
    return _normalizar_mid(a.merchant_id) if a else ''


def transacoes_do_mid(mid):
    """As transacções que um ficheiro deste Merchant ID pode reconciliar: as das lojas com esse contrato e, se for o
    da Bendi, as da Bendi (loja vazia). Um ficheiro nunca toca nas transacções de outro comerciante."""
    from django.db.models import Q
    from ..models import TransacaoVinti4
    mid = _normalizar_mid(mid)
    filtro = Q(loja_id__in=lojas_do_mid(mid))
    if mid and mid == _normalizar_mid(settings.VINTI4_MERCHANT_ID):
        filtro |= Q(loja__isnull=True)
    return TransacaoVinti4.objects.filter(filtro)


def _ultimo(mid):
    from ..models import FicheiroVBVT
    return (FicheiroVBVT.objects.filter(merchant_id=mid, estado='aplicado')
            .order_by('-data', '-sequencia', '-id').first())


def _d(v):
    return v.strftime('%d/%m/%Y') if isinstance(v, date) else '—'


# ── reconciliação ──────────────────────────────────────────────

def _comparar(n, tipo, c, txs):
    """Uma linha de detalhe → dict com o resultado (e o que mudar na transacção)."""
    linha = {'linha': n, 'tipo': TIPOS_REGISTO[tipo], 'ref': c['ref'], 'message_id': c['message_id'],
             'aprovada': c['rt'] == '0', 'quando': c['quando'].strftime('%Y-%m-%d %H:%M:%S'),
             'transacao': f'{c["periodo"]}-{c["tid"]}', 'pan': c.get('pan', ''), 'valor': str(c['valor']),
             'comissao': str(c['comissao']) if c.get('comissao') is not None else '', 'cartao': c.get('cartao', ''),
             'tx_id': None}
    if tipo == '3':
        linha['resultado'] = 'nao_aplicavel'
        return linha
    if tipo == '2':
        linha['ref_original'] = c['ref_original']
        tx = txs.get(c['ref_original']) or txs.get(c['ref'])
        if not tx:
            linha['resultado'] = 'desconhecida'
            return linha
        linha['tx_id'] = tx.id
        linha['resultado'] = 'estorno' if c['rt'] == '0' else 'estorno_recusado'
        return linha
    tx = txs.get(c['ref'])
    if not tx:
        linha['resultado'] = 'desconhecida'
        return linha
    linha['tx_id'] = tx.id
    if c['rt'] == '0':
        if tx.estado != 'paga':
            linha['resultado'] = 'paga_so_na_sisp'
        elif c['valor'] != Decimal(tx.montante):
            linha['resultado'] = 'valor_diferente'
            linha['valor_nosso'] = str(tx.montante)
        else:
            linha['resultado'] = 'ok'
    else:
        linha['resultado'] = 'paga_so_ca' if tx.estado == 'paga' else 'recusada'
    return linha


def processar(conteudo, nome='', utilizador=None, forcar=False, loja=None):
    """Valida e aplica um ficheiro VBVT → FicheiroVBVT (aplicado ou rejeitado; fica sempre registado).
    loja: carregado no backoffice dessa loja — só se aceita o ficheiro do Merchant ID do contrato dela."""
    from ..models import FicheiroVBVT, TransacaoVinti4
    from ..utils.registo import registar
    if len(conteudo) > TAMANHO_MAX:
        raise ErroVBVT('O ficheiro é demasiado grande (máximo 5 MB).')
    hash_ = hashlib.sha256(conteudo).hexdigest()
    lido = ler(conteudo)
    erros, avisos = list(lido['erros']), []
    h = lido['header'] or {}
    mid = _normalizar_mid(h.get('merchant_id')) if h else ''
    quem = None
    mid_registo = mid          # carregado por uma loja com o ficheiro de outro comerciante: fica registado na loja
    with transaction.atomic():
        # um ficheiro de cada vez por Merchant ID (a sequência depende do último aplicado)
        if mid:
            with connection.cursor() as cur:
                cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))', [f'vbvt:{mid}'])
        if h:
            quem = dono(mid)
            if loja is not None and mid != mid_da_loja(loja):
                mid_registo, quem = mid_da_loja(loja), ('loja', loja)
                erros.append({'linha': 1, 'erro': f'Este ficheiro é do Merchant ID {mid}, que não é o do contrato vinti4 '
                                                  f'desta loja — descarrega o ficheiro no Portal do Comerciante da loja.'})
            elif quem is None:
                erros.append({'linha': 1, 'erro': f'Merchant ID {mid} desconhecido: não é o da Bendi (VINTI4_MERCHANT_ID) '
                                                  f'nem o de nenhuma loja com contrato vinti4.'})
            repetido = FicheiroVBVT.objects.filter(hash=hash_, estado='aplicado').first()
            if repetido:
                erros.append({'linha': 0, 'erro': f'Este ficheiro já foi processado em '
                                                  f'{timezone.localtime(repetido.carregado_em):%d/%m/%Y %H:%M}.'})
            elif FicheiroVBVT.objects.filter(merchant_id=mid, data=h['data'], sequencia=h['sequencia'],
                                             estado='aplicado').exists():
                erros.append({'linha': 1, 'erro': f'O ficheiro de {_d(h["data"])} nº {h["sequencia"]:03d} deste Merchant ID '
                                                  f'já foi processado (conteúdo diferente — pedir esclarecimento à SISP).'})
            ultimo = _ultimo(mid) if mid else None
            if ultimo and not repetido:
                anterior = (h.get('data_anterior'), h.get('sequencia_anterior'))
                if anterior != (ultimo.data, ultimo.sequencia):
                    msg = (f'Sequência: este ficheiro diz que o anterior é o de {_d(anterior[0])} nº '
                           f'{(anterior[1] or 0):03d}, mas o último processado é o de {_d(ultimo.data)} nº '
                           f'{ultimo.sequencia:03d} — falta pelo menos um ficheiro ou está fora de ordem.')
                    (avisos if forcar else erros).append({'linha': 1, 'erro': msg})
                elif (h['data'], h['sequencia']) <= (ultimo.data, ultimo.sequencia):
                    msg = 'Sequência: este ficheiro não é posterior ao último processado.'
                    (avisos if forcar else erros).append({'linha': 1, 'erro': msg})
        linhas, resumo = [], {}
        if not erros:
            refs = set()
            for _, tipo, c in lido['detalhes']:
                refs.update(r for r in (c['ref'], c.get('ref_original')) if r)
            txs = {t.ref: t for t in transacoes_do_mid(mid).select_for_update()
                   .filter(ref__in=[r for r in refs if len(r) <= 15])}
            por_id = {t.id: t for t in txs.values()}
            agora = timezone.now()
            mudadas, estornadas = {}, {}       # estornadas: tx.pk → nº das transacções de estorno na SISP
            for n, tipo, c in lido['detalhes']:
                linha = _comparar(n, tipo, c, txs)
                linhas.append(linha)
                tx = por_id.get(linha['tx_id'])
                if not tx:
                    continue
                if tipo == '1' and linha['resultado'] in ('ok', 'valor_diferente'):
                    tx.reconciliada_em = agora
                    tx.comissao_sisp = c.get('comissao')
                    tx.tipo_cartao = (c.get('cartao') or '')[:5]
                    if not tx.tid:          # confirmada pela API de estado: o ficheiro traz o nº da transacção
                        # o período e o tid NÃO se mudam: tx.transacao ('v4_<ref>' sem tid) já foi gravado no
                        # Pagamento/Fatura e é a chave que reconhece o mesmo pagamento num regresso posterior —
                        # mudá-lo fazia parecer um pagamento a dobrar. O nº da SISP fica na linha do ficheiro.
                        tx.message_id = tx.message_id or c['message_id'][:20]
                        tx.pan = tx.pan or (c.get('pan') or '')[:21]
                    mudadas[tx.pk] = tx
                elif tipo == '2' and linha['resultado'] == 'estorno':
                    tx.estornada_em = tx.estornada_em or agora
                    tx.valor_estornado += c['valor']        # um ficheiro só se aplica uma vez: não conta a dobrar
                    estornadas.setdefault(tx.pk, []).append(f'{c["periodo"]}-{c["tid"]}')
                    mudadas[tx.pk] = tx
            for tx in mudadas.values():
                tx._sem_tempo_real = True       # o tempo real avisa uma vez, pelo FicheiroVBVT criado
                tx.save(update_fields=['reconciliada_em', 'comissao_sisp', 'tipo_cartao', 'periodo', 'tid',
                                       'message_id', 'pan', 'estornada_em', 'valor_estornado'])
            # reforço dos reembolsos: o estorno que a SISP fez confirma (e fecha) o pedido de reembolso
            from ..utils.devolucoes import avisar_estornos_em_falta, confirmar_estornos_sisp
            for pk, numeros in estornadas.items():
                confirmar_estornos_sisp(mudadas[pk], h.get('data'), numeros)
            avisar_estornos_em_falta(lojas_do_mid(mid), h.get('data'))
            compras = [(l, c) for l, (_, t, c) in zip(linhas, lido['detalhes']) if t == '1' and c['rt'] == '0']
            estornos = [(l, c) for l, (_, t, c) in zip(linhas, lido['detalhes']) if t == '2' and c['rt'] == '0']
            total = sum((c['valor'] for _, c in compras), Decimal('0'))
            comissoes = sum((c['comissao'] or Decimal('0') for _, c in compras + estornos), Decimal('0'))
            estornado = sum((c['valor'] for _, c in estornos), Decimal('0'))
            contagem = {}
            for l in linhas:
                contagem[l['resultado']] = contagem.get(l['resultado'], 0) + 1
            resumo = {'registos': len(linhas), 'compras_aprovadas': len(compras), 'total_compras': str(total),
                      'estornos': len(estornos), 'total_estornos': str(estornado), 'comissoes': str(comissoes),
                      'liquido': str(total - estornado - comissoes), 'resultados': contagem,
                      'problemas': sum(contagem.get(k, 0) for k in PROBLEMAS)}
        f = FicheiroVBVT.objects.create(
            nome=str(nome or '')[:200], hash=hash_, merchant_id=mid_registo[:15],
            loja=quem[1] if quem else None, data=h.get('data'), sequencia=h.get('sequencia'),
            data_anterior=h.get('data_anterior'), sequencia_anterior=h.get('sequencia_anterior'),
            estado='rejeitado' if erros else 'aplicado', forcado=bool(forcar and avisos and not erros),
            erros=erros[:500], avisos=avisos, resumo=resumo, linhas=linhas[:MAX_LINHAS_GUARDADAS],
            carregado_por=utilizador)
        registar('vinti4', f'vbvt_{f.estado}', objeto_id=f.id, loja_id=f.loja_id,
                 referencia=f'vbvt-{mid}-{h.get("data") or ""}-{h.get("sequencia") or ""}',
                 dados={'nome': f.nome[:80], 'hash': hash_[:16], 'erros': len(erros), 'forcado': f.forcado,
                        'problemas': resumo.get('problemas', 0)})
        if f.estado == 'aplicado':
            _avisar_diferencas(f, mid)
    return f


# as diferenças que são dinheiro (não as linhas que não são nossas): avisam o dono do contrato e os admins
DINHEIRO = ('paga_so_na_sisp', 'paga_so_ca', 'valor_diferente')


def _avisar_diferencas(f, mid):
    from ..models import Loja
    from ..utils.fila_emails import IMPORTANTE
    from ..Views.notificacaoView import notificar_admins, notificar_staff
    n = sum((f.resumo.get('resultados') or {}).get(k, 0) for k in DINHEIRO)
    if not n:
        return
    titulo = f'Reconciliação do cartão: {n} pagamento(s) com diferenças'
    msg = (f'O ficheiro VBVT de {_d(f.data)} nº {(f.sequencia or 0):03d} tem {n} pagamento(s) que não batem com o site '
           f'(ex.: aprovado na SISP e não pago cá). Abre a reconciliação e usa "Perguntar à SISP".')
    chave = f'vbvt:{f.id}'
    for loja in Loja.objects.filter(id__in=lojas_do_mid(mid)):
        notificar_staff(loja, ['dono'], 'vinti4', titulo, msg, link=f'/loja/{loja.id}/backoffice/pagamentos',
                        email=IMPORTANTE, email_chave=chave)
    notificar_admins('vinti4', titulo, msg, loja=f.loja, link='/admin/pagamentos', email=IMPORTANTE, email_chave=chave)


def relatorio(f):
    """Texto para mandar à SISP (Plan Test 36–37: 'resultado do processamento')."""
    r = f.resumo or {}
    linhas = [
        f'Ficheiro VBVT: {f.nome or "(sem nome)"}',
        f'Merchant ID: {f.merchant_id or "—"} · Data: {_d(f.data)} · Sequência: {(f.sequencia or 0):03d} · '
        f'Anterior: {_d(f.data_anterior)} nº {(f.sequencia_anterior or 0):03d}',
        f'Processado em: {timezone.localtime(f.carregado_em):%d/%m/%Y %H:%M}',
        f'Resultado: {f.get_estado_display().upper()}' + (' (sequência aceite manualmente)' if f.forcado else ''),
    ]
    if f.erros:
        linhas.append('Erros:')
        linhas += [f'  - linha {e["linha"]}: {e["erro"]}' for e in f.erros]
    if f.avisos:
        linhas.append('Avisos:')
        linhas += [f'  - linha {e["linha"]}: {e["erro"]}' for e in f.avisos]
    if r:
        linhas.append(f'Registos de detalhe: {r.get("registos", 0)} · compras aprovadas: {r.get("compras_aprovadas", 0)} '
                      f'({r.get("total_compras")} CVE) · estornos: {r.get("estornos", 0)} ({r.get("total_estornos")} CVE) · '
                      f'comissões: {r.get("comissoes")} CVE · líquido: {r.get("liquido")} CVE')
        for k, n in (r.get('resultados') or {}).items():
            linhas.append(f'  {RESULTADOS.get(k, k)}: {n}')
        problemas = [l for l in f.linhas if l['resultado'] in PROBLEMAS]
        if problemas:
            linhas.append('Diferenças:')
            linhas += [f'  - linha {l["linha"]}: {l["ref"]} {l["valor"]} CVE — {RESULTADOS[l["resultado"]]}'
                       for l in problemas[:200]]
    return '\n'.join(linhas)
