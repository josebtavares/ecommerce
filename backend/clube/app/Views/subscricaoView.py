"""
Subscrições das lojas (utils/subscricoes.py):
  público     → planos para a criação da loja
  backoffice  → ver a subscrição/comissão, mensalidades paginadas, pagar faturas (simulado), renovação automática
  admin       → planos, lista das lojas e faturas, marcar paga à mão, mudar o modelo de uma loja
"""
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from ..models import FaturaSubscricao, Loja, PlanoSubscricao, Subscricao
from ..utils import subscricoes as subs
from ..utils.pagination import paginar_lista
from .adminView import _exige_admin
from .lojaView import _exige_permissao


def _erro(msg, codigo=status.HTTP_400_BAD_REQUEST):
    return Response({'detail': msg}, status=codigo)


def _inteiro(v):
    """Um número inteiro vindo do pedido (7 ou "7"); 0 para o resto — True, 1.5, "abc", listas…"""
    if isinstance(v, bool):
        return 0
    if isinstance(v, int):
        return v
    if isinstance(v, str) and v.strip().lstrip('-').isdigit() and len(v.strip()) < 10:
        return int(v)
    return 0


# ── Cobranças paginadas (admin, backoffice da loja e do POS) ──

def filtrar_cobrancas(request, qs):
    """
    ?estado=pendente|paga|anulada|atraso  ?q= S-12 / 12 / descrição / nº da fatura do Bende / referência / notas
    ?de=&ate= AAAA-MM-DD (início do período). Devolve (qs, erro).
    """
    from datetime import date
    estado = request.GET.get('estado') or ''
    if estado == 'atraso':
        qs = qs.filter(estado='pendente', vencimento__lt=subs.hoje())
    elif estado in dict(FaturaSubscricao.ESTADOS):
        qs = qs.filter(estado=estado)
    q = (request.GET.get('q') or '').strip()
    if q:
        num = q.upper().removeprefix('S-').removeprefix('#').strip()
        filtro = (Q(descricao__icontains=q) | Q(fatura_numero__icontains=q) | Q(referencia__icontains=q) |
                  Q(notas__icontains=q) | Q(loja__nome__icontains=q) | Q(pos__nome__icontains=q) | Q(pos__codigo_pos__icontains=q))
        if num.isdigit() and len(num) < 10:
            filtro |= Q(id=int(num))
        qs = qs.filter(filtro)
    try:
        if request.GET.get('de'):
            qs = qs.filter(periodo_inicio__gte=date.fromisoformat(request.GET['de']))
        if request.GET.get('ate'):
            qs = qs.filter(periodo_inicio__lte=date.fromisoformat(request.GET['ate']))
    except ValueError:
        return qs, _erro('Datas inválidas (AAAA-MM-DD).')
    return qs, None


def pagina_cobrancas(request, qs, limite=20):
    """{count, results} paginado na base de dados (?limit= até 100, ?offset=)."""
    qs, erro = filtrar_cobrancas(request, qs)
    if erro:
        return erro
    try:
        limit = min(max(int(request.GET.get('limit') or limite), 1), 100)
        offset = max(int(request.GET.get('offset') or 0), 0)
    except ValueError:
        return _erro('offset/limit inválidos.')
    qs = qs.select_related('loja', 'pos', 'plano')
    return Response({'count': qs.count(), 'results': [subs.fatura_payload(f) for f in qs[offset:offset + limit]]})


def _lojas_qs():
    return Loja.objects.exclude(estado='pendente', modelo_cobranca='comissao').select_related(
        'subscricao__plano', 'subscricao_servicos__plano').annotate(
        n_pendentes=Count('faturas_subscricao', filter=Q(faturas_subscricao__estado='pendente')),
        v_pendente=Sum('faturas_subscricao__valor', filter=Q(faturas_subscricao__estado='pendente')))


def _linha_loja(l):
    sub = getattr(l, 'subscricao', None) if l.modelo_cobranca == 'subscricao' else None
    serv = getattr(l, 'subscricao_servicos', None)
    return {'loja_id': l.id, 'loja_nome': l.nome, 'loja_estado': l.estado, 'modelo': l.modelo_cobranca,
            'percentagem_comissao': str(l.percentagem_comissao), 'subscricao': subs.subscricao_payload(sub),
            'subscricao_servicos': subs.subscricao_payload(serv) if serv and serv.estado != 'cancelada' else None,
            'faturas_pendentes': l.n_pendentes, 'valor_pendente': str(l.v_pendente or 0)}


def _pos_qs():
    from ..pos.models import ConfiguracaoPOS
    return ConfiguracaoPOS.objects.select_related(
        'dono__user', 'loja_vinculada', 'subscricao__plano', 'subscricao__plano_seguinte', 'subscricao__coberta_por__loja',
        'subscricao__coberta_por__plano').annotate(
        n_pendentes=Count('faturas_subscricao', filter=Q(faturas_subscricao__estado='pendente')),
        v_pendente=Sum('faturas_subscricao__valor', filter=Q(faturas_subscricao__estado='pendente')))


def _linha_pos(p):
    sub = getattr(p, 'subscricao', None)
    cob = sub.coberta_por if sub and sub.coberta_por_id else None
    return {'pos_id': p.id, 'pos_nome': subs.nome_alvo(p), 'nome': p.nome, 'codigo_pos': p.codigo_pos,
            'dono': p.dono.user.get_full_name() or p.dono.user.username, 'dono_email': p.dono.user.email,
            'loja_vinculada': p.loja_vinculada.nome if p.loja_vinculada_id else None,
            'loja_vinculada_id': p.loja_vinculada_id,
            'suspenso': p.suspenso, 'suspenso_motivo': p.suspenso_motivo,
            'subscricao': subs.subscricao_payload(sub),
            'cobertura': {'loja_id': cob.loja_id, 'loja_nome': cob.loja.nome, 'plano': cob.plano.nome if cob.plano_id else ''} if cob else None,
            'faturas_pendentes': p.n_pendentes, 'valor_pendente': str(p.v_pendente or 0)}


@api_view(['GET'])
@permission_classes([AllowAny])
def planos_publicos(request):
    """GET /app/planos/ — planos activos + a comissão por defeito (formulário "Criar loja")."""
    from ..models import ConfiguracaoPlataforma
    return Response({
        'comissao_padrao': str(Loja._meta.get_field('percentagem_comissao').default),
        'dias_teste': ConfiguracaoPlataforma.atual().subscricao_dias_teste,
        'planos': [subs.plano_payload(p) for p in subs.planos_ativos()],
    })


# ── Backoffice ────────────────────────────────────────────────

def _resumo_loja(loja, membro):
    from ..servicos import cobranca
    sub = Subscricao.objects.select_related('plano').filter(loja=loja).first()
    sub_serv = Subscricao.objects.select_related('plano').filter(loja_servicos=loja).first()
    # as faturas da loja e as da subscrição de Serviços aparecem juntas
    # a lista completa (paginada, com pesquisa) é /app/loja/<id>/subscricao/faturas/; aqui só as últimas
    faturas = list(loja.faturas_subscricao.select_related('plano')[:10]) if (sub or sub_serv) else []
    pendentes_todas = list(loja.faturas_subscricao.filter(estado='pendente').select_related('plano'))
    pendentes = [f for f in pendentes_todas if sub and f.subscricao_id == sub.id]
    pend_serv = [f for f in pendentes_todas if sub_serv and f.subscricao_id == sub_serv.id]
    livre = subs.proxima_troca(loja)
    pedido = None
    if sub and sub.estado == 'aguarda' and loja.modelo_cobranca == 'comissao':
        f = next((x for x in pendentes), None)
        pedido = {'plano': subs.plano_payload(sub.plano), 'fatura': subs.fatura_payload(f) if f else None}
    return {
        'modelo': loja.modelo_cobranca,
        'aviso': subs.aviso_loja(sub, pendentes) if loja.modelo_cobranca == 'subscricao' else None,
        # trocas: só uma a cada 3 meses; pedido = mudança para subscrição à espera da 1.ª fatura
        'troca_livre_em': livre.isoformat() if livre else None,
        'pedido': pedido,
        'percentagem_comissao': str(loja.percentagem_comissao),
        'subscricao': subs.subscricao_payload(sub),
        'faturas': [subs.fatura_payload(f) for f in faturas],
        'por_pagar': str(sum((f.valor for f in pendentes_todas), Decimal('0'))),
        # módulo Serviços: incluído na subscrição ou com subscrição própria (lojas em comissão)
        'servicos': {**cobranca.resumo(loja),
                     'aviso': subs.aviso_loja(sub_serv, pend_serv) if sub_serv else None},
        'pode_pagar': membro.pode('pagar_subscricao'),
        'planos': [subs.plano_payload(p) for p in subs.planos_ativos()],
        # os POS do dono ligados a esta loja (o plano Loja + POS inclui-os)
        'pos_ligados': [{'id': p.id, 'nome': p.nome, 'codigo': p.codigo_pos,
                         'incluido': bool(sub) and getattr(getattr(p, 'subscricao', None), 'coberta_por_id', None) == sub.id}
                        for p in loja.pos_vinculados.filter(dono_id=loja.dono_id).select_related('subscricao')],
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def loja_subscricao_faturas(request, loja_id):
    """GET /app/loja/<loja_id>/subscricao/faturas/?estado=&q=&de=&ate=&limit=&offset= — todas as mensalidades da loja."""
    loja = get_object_or_404(Loja, id=loja_id)
    membro, erro = _exige_permissao(request, loja, 'ver_subscricao')
    if erro:
        return erro
    return pagina_cobrancas(request, loja.faturas_subscricao.all(), limite=10)


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def loja_subscricao(request, loja_id):
    """
    GET   /app/loja/<loja_id>/subscricao/   (dono, gestor, contabilista)
    PATCH /app/loja/<loja_id>/subscricao/   { auto_renovar }   (só o dono)
    """
    loja = get_object_or_404(Loja, id=loja_id)
    membro, erro = _exige_permissao(request, loja, 'ver_subscricao')
    if erro:
        return erro
    if request.method == 'PATCH':
        if not membro.pode('pagar_subscricao'):
            return _erro('Só o dono da loja gere a subscrição.', status.HTTP_403_FORBIDDEN)
        sub = Subscricao.objects.filter(loja=loja).exclude(estado='cancelada').first()
        if not sub:
            return _erro('Esta loja não está em subscrição.')
        valor = request.data.get('auto_renovar')
        if not isinstance(valor, bool):
            return _erro('auto_renovar inválido.')
        sub.auto_renovar = valor
        sub.save(update_fields=['auto_renovar', 'data_atualizacao'])
    return Response(_resumo_loja(loja, membro))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def loja_fatura_pagar(request, loja_id, fatura_id):
    """POST /app/loja/<loja_id>/subscricao/faturas/<fatura_id>/pagar/ — pagamento (simulado) pelo dono."""
    loja = get_object_or_404(Loja, id=loja_id)
    membro, erro = _exige_permissao(request, loja, 'pagar_subscricao')
    if erro:
        return erro
    fatura = get_object_or_404(FaturaSubscricao, id=fatura_id, loja=loja)
    try:
        subs.pagar(fatura, 'simulado', referencia=f'SIM-{fatura.id}')
    except subs.ErroFatura as e:
        return _erro(str(e))
    loja.refresh_from_db()          # pagar pode ter mudado o modelo (pedido de mudança) ou reactivado a loja
    return Response(_resumo_loja(loja, membro))


# ── Admin ─────────────────────────────────────────────────────

def _ler_plano(dados, plano=None):
    """Valida os campos de um plano. Devolve (campos, None) ou (None, mensagem)."""
    campos = {}
    if 'nome' in dados or plano is None:
        nome = str(dados.get('nome') or '').strip()
        if not nome or len(nome) > 80:
            return None, 'Dá um nome ao plano (até 80 caracteres).'
        campos['nome'] = nome
    if 'periodicidade' in dados or plano is None:
        if dados.get('periodicidade') not in PlanoSubscricao.MESES:
            return None, 'Periodicidade inválida (mensal, trimestral ou anual).'
        campos['periodicidade'] = dados['periodicidade']
    if 'tipo' in dados or plano is None:
        tipo = dados.get('tipo') or 'loja'
        if tipo not in dict(PlanoSubscricao.TIPOS):
            return None, 'Tipo inválido (loja, pos, loja_pos ou servicos).'
        campos['tipo'] = tipo
    for chave, maximo in (('limite_marcacoes_mes', 100000), ('limite_profissionais', 1000)):
        if chave in dados:
            v = dados.get(chave)
            if v in (None, ''):
                campos[chave] = None
            elif isinstance(v, bool) or not str(v).strip().isdigit() or not 1 <= int(v) <= maximo:
                return None, 'Limite inválido (vazio = sem limite).'
            else:
                campos[chave] = int(v)
    if 'preco' in dados or plano is None:
        try:
            preco = Decimal(str(dados.get('preco'))).quantize(Decimal('0.01'))
        except (InvalidOperation, TypeError, ValueError):
            return None, 'Preço inválido.'
        if not preco.is_finite() or preco < 0 or preco > Decimal('10000000'):
            return None, 'Preço inválido.'
        campos['preco'] = preco
    if 'descricao' in dados:
        campos['descricao'] = str(dados.get('descricao') or '').strip()[:300]
    if 'ativo' in dados:
        if not isinstance(dados['ativo'], bool):
            return None, 'ativo inválido.'
        campos['ativo'] = dados['ativo']
    if 'ordem' in dados:
        try:
            campos['ordem'] = max(0, min(int(dados['ordem']), 999))
        except (TypeError, ValueError):
            return None, 'Ordem inválida.'
    return campos, None


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def admin_planos(request):
    """GET/POST /app/admin/planos/"""
    erro = _exige_admin(request, 'gerir_subscricoes')
    if erro:
        return erro
    if request.method == 'POST':
        campos, msg = _ler_plano(request.data)
        if msg:
            return _erro(msg)
        p = PlanoSubscricao.objects.create(**campos)
        return Response(subs.plano_payload(p), status=status.HTTP_201_CREATED)
    planos = PlanoSubscricao.objects.annotate(n_lojas=Count('subscricoes', filter=~Q(subscricoes__estado='cancelada')))
    return Response([{**subs.plano_payload(p), 'lojas': p.n_lojas} for p in planos])


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def admin_plano(request, plano_id):
    """PATCH /app/admin/planos/<id>/ — o preço novo só vale para quem escolher o plano depois."""
    erro = _exige_admin(request, 'gerir_subscricoes')
    if erro:
        return erro
    plano = get_object_or_404(PlanoSubscricao, id=plano_id)
    campos, msg = _ler_plano(request.data, plano)
    if msg:
        return _erro(msg)
    if 'periodicidade' in campos and campos['periodicidade'] != plano.periodicidade and plano.subscricoes.exists():
        return _erro('Este plano já tem lojas — cria um plano novo para mudar a periodicidade.')
    if 'tipo' in campos and campos['tipo'] != plano.tipo and (plano.subscricoes.exists() or plano.faturas.exists()):
        return _erro('Este plano já foi usado — cria um plano novo para outro tipo.')
    for k, v in campos.items():
        setattr(plano, k, v)
    plano.save()
    return Response(subs.plano_payload(plano))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_subscricoes(request):
    """
    GET /app/admin/subscricoes/?modelo=subscricao|comissao&estado=…&q=…&offset&limit
    As lojas com o modelo de cobrança, a subscrição e o que têm por pagar.
    """
    erro = _exige_admin(request, 'gerir_subscricoes')
    if erro:
        return erro
    qs = _lojas_qs()
    modelo = request.GET.get('modelo')
    if modelo in ('comissao', 'subscricao'):
        qs = qs.filter(modelo_cobranca=modelo)
    estado = request.GET.get('estado')
    if estado in dict(Subscricao.ESTADOS):
        qs = qs.filter(subscricao__estado=estado, modelo_cobranca='subscricao')
    q = (request.GET.get('q') or '').strip()
    if q:
        qs = qs.filter(nome__icontains=q)
    return paginar_lista(request, [_linha_loja(l) for l in qs.order_by('-modelo_cobranca', 'nome')])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_faturas(request):
    """
    GET /app/admin/faturas/?loja=<id>[&com_pos=1]&pos=<id>&tipo=loja|servicos|pos&estado=pendente|paga|anulada|atraso
                           &q=&de=&ate=&limit=&offset=   — cobranças (mensalidades), paginadas na base de dados.
    """
    erro = _exige_admin(request, 'gerir_subscricoes')
    if erro:
        return erro
    qs = FaturaSubscricao.objects.all()
    if (request.GET.get('loja') or '').isdigit():
        loja_id = int(request.GET['loja'])
        qs = qs.filter(Q(loja_id=loja_id) | Q(pos__loja_vinculada_id=loja_id)) if request.GET.get('com_pos') == '1' else qs.filter(loja_id=loja_id)
    if (request.GET.get('pos') or '').isdigit():
        qs = qs.filter(pos_id=int(request.GET['pos']))
    if request.GET.get('tipo') == 'loja':
        qs = qs.filter(loja__isnull=False, subscricao__loja_servicos__isnull=True)
    elif request.GET.get('tipo') == 'servicos':
        qs = qs.filter(subscricao__loja_servicos__isnull=False)
    elif request.GET.get('tipo') == 'pos':
        qs = qs.filter(pos__isnull=False)
    return pagina_cobrancas(request, qs)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_subscricoes_abas(request):
    """
    GET /app/admin/subscricoes/abas/?q=&limit=&offset=&fixar=loja-12 — abas das Subscrições: lojas e POS sem loja,
    com as cobranças por pagar (as em atraso primeiro). As de um POS ligado contam na loja.
    """
    erro = _exige_admin(request, 'gerir_subscricoes')
    if erro:
        return erro
    from ..pos.models import ConfiguracaoPOS
    from .faturacaoView import abas_resposta, procura_abas
    lojas = Loja.objects.exclude(estado='pendente', modelo_cobranca='comissao')
    poss = ConfiguracaoPOS.objects.filter(loja_vinculada__isnull=True)
    q = (request.GET.get('q') or '').strip()
    if q:
        ql, qp = procura_abas(q)
        lojas, poss = lojas.filter(id__in=Loja.objects.filter(ql).values('id')), poss.filter(qp)
    pend, atraso = {}, {}
    hoje = subs.hoje()
    for loja_id, pos_loja, pos_id, venc in (FaturaSubscricao.objects.filter(estado='pendente').order_by()
                                            .values_list('loja_id', 'pos__loja_vinculada_id', 'pos_id', 'vencimento')):
        chave = ('loja', loja_id or pos_loja) if (loja_id or pos_loja) else ('pos', pos_id)
        pend[chave] = pend.get(chave, 0) + 1
        if venc < hoje:
            atraso[chave] = atraso.get(chave, 0) + 1
    itens = [{'tipo': 'loja', 'id': i, 'nome': n} for i, n in lojas.values_list('id', 'nome')]
    itens += [{'tipo': 'pos', 'id': i, 'nome': n, 'codigo_pos': c} for i, n, c in poss.values_list('id', 'nome', 'codigo_pos')]
    for i in itens:
        k = (i['tipo'], i['id'])
        i['contador'], i['em_atraso'] = pend.get(k, 0), atraso.get(k, 0)
        i['alerta'] = bool(i['em_atraso'])
    return abas_resposta(request, itens, prioridade='em_atraso')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_subscricao_ficha(request, tipo, id):
    """GET /app/admin/subscricoes/ficha/<loja|pos>/<id>/ — a loja (com os seus POS) ou o POS: modelo, plano, por pagar."""
    erro = _exige_admin(request, 'gerir_subscricoes')
    if erro:
        return erro
    from ..pos.models import ConfiguracaoPOS
    from ..utils import subscricoes_pos as subs_pos
    if tipo == 'loja':
        loja = get_object_or_404(_lojas_qs(), id=id)
        for p in ConfiguracaoPOS.objects.filter(loja_vinculada=loja):
            subs_pos.garantir(p)          # um POS acabado de ligar sem subscrição
        pos = _pos_qs().filter(loja_vinculada=loja).order_by('nome', 'id')
        return Response({'tipo': 'loja', 'loja': _linha_loja(loja), 'pos': [_linha_pos(p) for p in pos]})
    if tipo == 'pos':
        subs_pos.garantir(get_object_or_404(ConfiguracaoPOS, id=id))
        p = get_object_or_404(_pos_qs(), id=id)
        return Response({'tipo': 'pos', 'pos': _linha_pos(p),
                         'loja': {'id': p.loja_vinculada_id, 'nome': p.loja_vinculada.nome} if p.loja_vinculada_id else None})
    return _erro('Tipo inválido.', status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_fatura_pagar(request, fatura_id):
    """POST /app/admin/faturas/<id>/pagar/ { metodo: dinheiro|transferencia|oferta|outro, notas? } — pagamento à mão."""
    erro = _exige_admin(request, 'gerir_subscricoes')
    if erro:
        return erro
    fatura = get_object_or_404(FaturaSubscricao, id=fatura_id)
    metodo = request.data.get('metodo')
    if metodo not in ('dinheiro', 'transferencia', 'oferta', 'outro'):
        return _erro('Escolhe como foi pago: dinheiro, transferência, oferta ou outro.')
    try:
        subs.pagar(fatura, metodo, notas=str(request.data.get('notas') or '').strip())
    except subs.ErroFatura as e:
        return _erro(str(e))
    fatura.refresh_from_db()
    return Response(subs.fatura_payload(fatura))


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def admin_loja_cobranca(request, loja_id):
    """PATCH /app/admin/lojas/<id>/cobranca/ { modelo: comissao|subscricao, plano_id? } — o admin força o modelo."""
    erro = _exige_admin(request, 'gerir_subscricoes')
    if erro:
        return erro
    loja = get_object_or_404(Loja, id=loja_id)
    modelo = request.data.get('modelo')
    plano = None
    if modelo == 'subscricao':
        plano = subs.plano_ativo(request.data.get('plano_id'))
        if not plano:
            return _erro('Escolhe um plano activo.')
    try:
        with transaction.atomic():
            subs.mudar_modelo(loja, modelo, plano)
    except subs.ErroFatura as e:
        return _erro(str(e))
    loja.refresh_from_db()
    sub = Subscricao.objects.filter(loja=loja).first()
    return Response({'loja_id': loja.id, 'modelo': loja.modelo_cobranca, 'subscricao': subs.subscricao_payload(sub)})


# ── Fase 3: trocas pedidas pelo dono, acções do admin, resumo ──

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def loja_subscricao_mudar(request, loja_id):
    """
    POST /app/loja/<loja_id>/subscricao/mudar/   (só o dono)
      { acao: 'subscricao', plano_id }  → pede a mudança de comissão para subscrição (1.ª fatura vence hoje)
      { acao: 'cancelar_pedido' }       → desiste desse pedido
      { acao: 'comissao' }              → passa para comissão no fim do período pago
      { acao: 'cancelar_comissao' }     → desiste dessa mudança
      { acao: 'plano', plano_id }       → muda de plano a partir da renovação
    """
    loja = get_object_or_404(Loja, id=loja_id)
    membro, erro = _exige_permissao(request, loja, 'pagar_subscricao')
    if erro:
        return erro
    acao = request.data.get('acao')
    plano = None
    if acao in ('subscricao', 'plano'):
        plano = subs.plano_ativo(request.data.get('plano_id'))
        if not plano:
            return _erro('Escolhe um dos planos disponíveis.')
    try:
        if acao == 'subscricao':
            subs.pedir_subscricao(loja, plano)
        elif acao == 'cancelar_pedido':
            subs.cancelar_pedido(loja)
        elif acao == 'comissao':
            subs.agendar_comissao(loja)
        elif acao == 'cancelar_comissao':
            subs.cancelar_agendamento(loja)
        elif acao == 'plano':
            subs.mudar_plano(loja, plano)
        else:
            return _erro('Acção inválida.')
    except subs.ErroFatura as e:
        return _erro(str(e))
    loja.refresh_from_db()
    return Response(_resumo_loja(loja, membro))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_oferecer(request, loja_id):
    """POST /app/admin/lojas/<id>/subscricao/oferecer/ { meses: 1-12, motivo?, servicos? } — servicos: a de Serviços"""
    erro = _exige_admin(request, 'gerir_subscricoes')
    if erro:
        return erro
    if request.data.get('servicos') is True:
        sub = get_object_or_404(Subscricao, loja_servicos_id=loja_id)
    else:
        sub = get_object_or_404(Subscricao, loja_id=loja_id)
    meses = _inteiro(request.data.get('meses'))
    if not 1 <= meses <= 12:
        return _erro('Oferece entre 1 e 12 meses.')
    try:
        f = subs.oferecer(sub, meses, str(request.data.get('motivo') or '').strip())
    except subs.ErroFatura as e:
        return _erro(str(e))
    return Response(subs.fatura_payload(f), status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_fatura_adiar(request, fatura_id):
    """POST /app/admin/faturas/<id>/adiar/ { dias: 1-60 }"""
    erro = _exige_admin(request, 'gerir_subscricoes')
    if erro:
        return erro
    fatura = get_object_or_404(FaturaSubscricao, id=fatura_id)
    dias = _inteiro(request.data.get('dias'))
    if not 1 <= dias <= 60:
        return _erro('Adia entre 1 e 60 dias.')
    try:
        f = subs.adiar(fatura, dias)
    except subs.ErroFatura as e:
        return _erro(str(e))
    return Response(subs.fatura_payload(f))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_fatura_anular(request, fatura_id):
    """POST /app/admin/faturas/<id>/anular/ { motivo }"""
    erro = _exige_admin(request, 'gerir_subscricoes')
    if erro:
        return erro
    fatura = get_object_or_404(FaturaSubscricao, id=fatura_id)
    motivo = str(request.data.get('motivo') or '').strip()
    if not motivo:
        return _erro('Escreve o motivo (fica registado na fatura).')
    try:
        f = subs.anular(fatura, motivo)
    except subs.ErroFatura as e:
        return _erro(str(e))
    return Response(subs.fatura_payload(f))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_resumo(request):
    """GET /app/admin/subscricoes/resumo/?inicio=AAAA-MM-DD&fim=AAAA-MM-DD — receita do período."""
    erro = _exige_admin(request, 'gerir_subscricoes')
    if erro:
        return erro
    from datetime import date
    try:
        inicio = date.fromisoformat(request.GET.get('inicio', ''))
        fim = date.fromisoformat(request.GET.get('fim', ''))
    except ValueError:
        return _erro('Indica inicio e fim (AAAA-MM-DD).')
    if fim < inicio or (fim - inicio).days > 3660:
        return _erro('Período inválido.')
    return Response(subs.resumo_periodo(inicio, fim))


# ── Admin: POS ────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_subscricoes_pos(request):
    """
    GET /app/admin/subscricoes/pos/?situacao=incluido|sem_plano|suspenso&estado=…&q=…&offset&limit
    Os POS com a subscrição, se estão incluídos no plano de uma loja e o que têm por pagar.
    """
    erro = _exige_admin(request, 'gerir_subscricoes')
    if erro:
        return erro
    from ..pos.models import ConfiguracaoPOS
    from ..utils import subscricoes_pos as subs_pos
    subs_pos.garantir_todos()               # um POS acabado de criar sem subscrição (o worker ainda não passou)
    qs = _pos_qs()
    situacao = request.GET.get('situacao')
    if situacao == 'incluido':
        qs = qs.filter(subscricao__coberta_por__isnull=False)
    elif situacao == 'sem_plano':
        qs = qs.filter(subscricao__plano__isnull=True, subscricao__coberta_por__isnull=True)
    elif situacao == 'suspenso':
        qs = qs.filter(suspenso=True)
    estado = request.GET.get('estado')
    if estado in dict(Subscricao.ESTADOS):
        qs = qs.filter(subscricao__estado=estado, subscricao__coberta_por__isnull=True)
    q = (request.GET.get('q') or '').strip()
    if q:
        qs = qs.filter(Q(nome__icontains=q) | Q(codigo_pos__icontains=q) | Q(dono__user__first_name__icontains=q)
                       | Q(dono__user__email__icontains=q))
    return paginar_lista(request, [_linha_pos(p) for p in qs.order_by('nome', 'id')])


def _sub_do_pos(pos_id):
    from ..pos.models import ConfiguracaoPOS
    from ..utils import subscricoes_pos as subs_pos
    return subs_pos.garantir(get_object_or_404(ConfiguracaoPOS, id=pos_id))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_pos_oferecer(request, pos_id):
    """POST /app/admin/pos/<pos_id>/subscricao/oferecer/ { meses: 1-12, motivo? }"""
    erro = _exige_admin(request, 'gerir_subscricoes')
    if erro:
        return erro
    sub = _sub_do_pos(pos_id)
    meses = _inteiro(request.data.get('meses'))
    if not 1 <= meses <= 12:
        return _erro('Oferece entre 1 e 12 meses.')
    try:
        f = subs.oferecer(sub, meses, str(request.data.get('motivo') or '').strip())
    except subs.ErroFatura as e:
        return _erro(str(e))
    return Response(subs.fatura_payload(f), status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_pos_plano(request, pos_id):
    """POST /app/admin/pos/<pos_id>/subscricao/plano/ { plano_id } — escolhe / muda o plano pelo dono (como na aba do POS)."""
    erro = _exige_admin(request, 'gerir_subscricoes')
    if erro:
        return erro
    from ..utils import subscricoes_pos as subs_pos
    sub = _sub_do_pos(pos_id)
    plano = subs.plano_ativo(request.data.get('plano_id'), tipos=('pos',))
    if not plano:
        return _erro('Escolhe um plano de POS activo.')
    try:
        subs_pos.escolher_plano(sub.pos, plano)
    except subs.ErroFatura as e:
        return _erro(str(e))
    sub.refresh_from_db()
    subs._avisar_dono(sub.pos, f'A plataforma mudou o plano do POS para {plano.nome}',
                      f'{subs._eur(plano.preco)} / {plano.get_periodicidade_display().lower()}. Vês os detalhes em POS → Subscrição.')
    return Response({'pos_id': sub.pos_id, 'subscricao': subs.subscricao_payload(sub)})
