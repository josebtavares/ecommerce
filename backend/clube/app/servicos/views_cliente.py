"""
Serviços — lado do cliente (etapa 3): ver os serviços da loja, horas livres, marcar, pagar
(simulado), as minhas marcações, cancelar e remarcar dentro do prazo, e a conversa com a loja
(mensagens, fotos, propostas de preço). A conversa serve também ao backoffice.
"""
from datetime import timedelta
from decimal import Decimal

from django.db.models import Q
from django.http import FileResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_ratelimit.core import is_ratelimited
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from ..models import Loja, Utilizador
from ..utils.dinheiro import formatar, ler_valor
from ..utils.horarios import fuso
from . import agenda, cobranca, conversa, pacotes
from . import marcacoes as ops
from .marcacoes import ErroMarcacao, marcacao_payload
from .models import FotoMarcacao, Marcacao, Profissional, Servico
from .views_backoffice import _ler_dia, _ler_dt, _quem, _texto, _url

MAX_ATIVAS_POR_LOJA = 5        # marcações futuras activas de um cliente na mesma loja
MINUTOS_PARA_PAGAR = 30


def _erro(msg, codigo=status.HTTP_400_BAD_REQUEST):
    return Response({'detail': msg}, status=codigo)


def _loja_disponivel(loja_id):
    loja = get_object_or_404(Loja.objects.select_related('config_servicos'), id=loja_id)
    return loja if cobranca.disponivel(loja) else None


def _limites_cliente(cfg):
    agora = timezone.now()
    return agora + timedelta(minutes=cfg.antecedencia_min), (agora.astimezone(fuso()).date() + timedelta(days=cfg.dias_max - 1))


# ══════════════════════════════════════════════════════════════
# PÚBLICO
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([AllowAny])
def publico(request, loja_id):
    """GET /app/lojas/<id>/servicos/publico/ — {disponivel, regras, servicos, profissionais}."""
    loja = get_object_or_404(Loja.objects.select_related('config_servicos'), id=loja_id)
    if not cobranca.disponivel(loja):
        return Response({'disponivel': False})
    cfg = loja.config_servicos
    servicos = list(pacotes.marcaveis(loja.servicos.all()).prefetch_related('imagens', 'profissionais', 'componentes__servico'))
    ativos = {p.id: p for p in loja.profissionais.filter(ativo=True)}
    return Response({
        'disponivel': True, 'loja': {'id': loja.id, 'nome': loja.nome, 'logo': _url(request, loja.logo)},
        'regras': {'cliente_escolhe_profissional': cfg.cliente_escolhe_profissional, 'cancelar_horas': cfg.cancelar_horas,
                   'reembolso_fora_prazo': cfg.reembolso_fora_prazo, 'confirmacao': cfg.confirmacao,
                   'dias_max': cfg.dias_max, 'antecedencia_min': cfg.antecedencia_min, 'minutos_para_pagar': MINUTOS_PARA_PAGAR},
        'servicos': [{
            'id': s.id, 'nome': s.nome, 'descricao': s.descricao, 'categoria': s.categoria, 'duracao_min': s.duracao_min,
            'tipo_preco': s.tipo_preco, 'preco': str(s.preco),
            'preco_texto': ('a partir de ' if s.tipo_preco == 'a_partir' else '') + formatar(s.preco),
            'pagamento': s.pagamento, 'imagens': [_url(request, i.ficheiro) for i in s.imagens.all()],
            **_pacote_publico(s),
            'profissionais': [p.id for p in s.profissionais.all() if p.id in ativos] if cfg.cliente_escolhe_profissional else [],
        } for s in servicos if any(p.id in ativos for p in s.profissionais.all())],
        'profissionais': [{'id': p.id, 'nome': p.nome, 'descricao': p.descricao, 'foto': _url(request, p.foto)}
                          for p in ativos.values()] if cfg.cliente_escolhe_profissional else [],
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def horas(request, loja_id):
    """GET /app/lojas/<id>/servicos/horas/?servico=&dia=&profissional= — horas livres (com a antecedência da loja)."""
    loja = _loja_disponivel(loja_id)
    if not loja:
        return _erro('Esta loja não está a aceitar marcações.', status.HTTP_404_NOT_FOUND)
    cfg = loja.config_servicos
    sid, dia = request.GET.get('servico') or '', _ler_dia(request.GET.get('dia'))
    if not sid.isdigit() or not dia:
        return _erro('Indica o serviço e o dia.')
    s = get_object_or_404(pacotes.marcaveis(Servico.objects.all()), id=int(sid), loja=loja)
    desde, ultimo = _limites_cliente(cfg)
    if dia > ultimo:
        return Response({'dia': dia.isoformat(), 'horas': [], 'fora_do_prazo': True})
    profs = s.profissionais.filter(ativo=True).prefetch_related('horarios').select_related('loja')
    pid = request.GET.get('profissional')
    if pid and cfg.cliente_escolhe_profissional:
        if not pid.isdigit():
            return _erro('profissional inválido.')
        profs = profs.filter(pk=int(pid))
    ops.expirar_vencidas(loja=loja)
    livres = agenda.horas_livres(s, dia, list(profs), desde=desde)
    # sem escolha de profissional o cliente só vê as horas
    return Response({'dia': dia.isoformat(), 'horas': [
        {'inicio': h['inicio'].isoformat(), **({'profissionais': h['profissionais']} if cfg.cliente_escolhe_profissional else {})}
        for h in livres]})


def _pacote_publico(s):
    """Num pacote: o que inclui e quanto custaria marcar cada serviço à parte."""
    if not s.e_pacote:
        return {'e_pacote': False}
    comps = [c.servico for c in s.componentes.all()]
    separado = sum((c.preco for c in comps), Decimal('0'))
    return {'e_pacote': True, 'componentes': [{'nome': c.nome, 'duracao_min': c.duracao_min} for c in comps],
            'valor_separado': str(separado), 'valor_separado_texto': formatar(separado),
            'poupanca_texto': formatar(separado - s.preco) if s.tipo_preco == 'fixo' and separado > s.preco else None}


def servico_card(request, s):
    imgs = list(s.imagens.all())
    return {'id': s.id, 'nome': s.nome, 'categoria': s.categoria, 'duracao_min': s.duracao_min, 'e_pacote': s.e_pacote,
            'preco_texto': ('a partir de ' if s.tipo_preco == 'a_partir' else '') + formatar(s.preco),
            'imagem': _url(request, imgs[0].ficheiro) if imgs else None,
            'loja': {'id': s.loja_id, 'nome': s.loja.nome, 'logo': _url(request, s.loja.logo), 'localizacao': s.loja.localizacao}}


@api_view(['GET'])
@permission_classes([AllowAny])
def pesquisa(request):
    """GET /app/servicos/pesquisa/?q=&offset=&limit= — serviços de todas as lojas (separador "Serviços" da pesquisa)."""
    qs = cobranca.servicos_publicos()
    q = (request.GET.get('q') or '').strip()[:80]
    if q:
        qs = qs.filter(Q(nome__icontains=q) | Q(categoria__icontains=q) | Q(descricao__icontains=q) | Q(loja__nome__icontains=q))
    try:
        offset = max(int(request.GET.get('offset') or 0), 0)
        limit = min(max(int(request.GET.get('limit') or 24), 1), 60)
    except ValueError:
        return _erro('Parâmetros inválidos.')
    total = qs.count()
    pagina = list(qs.order_by('-data_criacao', 'id')[offset:offset + limit])
    return Response({'count': total, 'results': [servico_card(request, s) for s in pagina],
                     'next_offset': offset + limit if offset + limit < total else None})


@api_view(['GET'])
@permission_classes([AllowAny])
def dias(request, loja_id):
    """
    GET /app/lojas/<id>/servicos/dias/?servico=&profissional= — os próximos dias (até 30, dentro do prazo da loja)
    com quantas horas livres têm: o cliente vê logo quais estão cheios e abre no primeiro com vagas.
    """
    loja = _loja_disponivel(loja_id)
    if not loja:
        return _erro('Esta loja não está a aceitar marcações.', status.HTTP_404_NOT_FOUND)
    cfg = loja.config_servicos
    sid = request.GET.get('servico') or ''
    if not sid.isdigit():
        return _erro('Indica o serviço.')
    s = get_object_or_404(pacotes.marcaveis(Servico.objects.all()), id=int(sid), loja=loja)
    profs = s.profissionais.filter(ativo=True).prefetch_related('horarios').select_related('loja')
    pid = request.GET.get('profissional')
    if pid and cfg.cliente_escolhe_profissional:
        if not pid.isdigit():
            return _erro('profissional inválido.')
        profs = profs.filter(pk=int(pid))
    profs = list(profs)
    desde, ultimo = _limites_cliente(cfg)
    ops.expirar_vencidas(loja=loja)
    hoje = timezone.now().astimezone(fuso()).date()
    out = []
    for i in range(min(cfg.dias_max, 30)):
        dia = hoje + timedelta(days=i)
        if dia > ultimo:
            break
        out.append({'dia': dia.isoformat(), 'livres': len(agenda.horas_livres(s, dia, profs, desde=desde))})
    return Response({'dias': out, 'primeiro_livre': next((d['dia'] for d in out if d['livres']), None)})


# ══════════════════════════════════════════════════════════════
# CLIENTE
# ══════════════════════════════════════════════════════════════

def _cliente_payload(request, m, completo=False):
    d = marcacao_payload(m, completo=False)
    for k in ('notas_internas', 'criada_por'):
        d.pop(k, None)
    cfg = m.loja.config_servicos
    d.update({'loja_id': m.loja_id, 'loja_nome': m.loja.nome, 'loja_logo': _url(request, m.loja.logo),
              'profissional_foto': _url(request, m.profissional.foto),
              'dentro_do_prazo': ops.dentro_do_prazo(m), 'cancelar_horas': cfg.cancelar_horas,
              'reembolso_fora_prazo': cfg.reembolso_fora_prazo,
              'pode_conversar': conversa.pode_conversar(m),
              'loja_indisponivel': not cobranca.disponivel(m.loja),
              'por_ler': conversa.por_ler(m, 'cliente')})
    if completo:
        d['mensagens'] = conversa.mensagens_payload(request, m, 'cliente')
        d['propostas'] = conversa.propostas_payload(m)
    return d


def _hora_proposta(servico, inicio, prof, desde):
    """A hora está entre as que se mostram ao cliente (para este profissional ou para algum do serviço)."""
    profs = [prof] if prof else list(servico.profissionais.filter(ativo=True).prefetch_related('horarios').select_related('loja'))
    dia = inicio.astimezone(fuso()).date()
    return any(h['inicio'] == inicio for h in agenda.horas_livres(servico, dia, profs, desde=desde))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def marcar(request, loja_id):
    """
    POST /app/lojas/<id>/servicos/marcar/ { servico_id, profissional_id?, inicio, pagamento: antecipado|local, notas? }
    Antecipado → pendente até pagar (30 min). No local → confirmada (ou pendente se a loja confirma à mão).
    """
    if is_ratelimited(request=request, group='servicos_marcar', key='user', rate='30/h', method='POST', increment=True):
        return _erro('Demasiadas marcações seguidas. Tenta mais tarde.', 429)
    loja = _loja_disponivel(loja_id)
    if not loja:
        return _erro('Esta loja não está a aceitar marcações.')
    cfg = loja.config_servicos
    u = request.user.utilizador
    d = request.data
    sid = d.get('servico_id')
    if isinstance(sid, bool) or not isinstance(sid, int):
        return _erro('Escolhe o serviço.')
    s = pacotes.marcaveis(Servico.objects.filter(loja=loja, id=sid)).first()
    if not s:
        return _erro('Este serviço já não está disponível.')
    prof = None
    pid = d.get('profissional_id')
    if pid not in (None, '') and cfg.cliente_escolhe_profissional:
        if isinstance(pid, bool) or not isinstance(pid, int):
            return _erro('Profissional inválido.')
        prof = s.profissionais.filter(ativo=True, pk=pid).select_related('loja').first()
        if not prof:
            return _erro('Esse profissional não faz este serviço.')
    inicio = _ler_dt(d.get('inicio'))
    if not inicio:
        return _erro('Escolhe o dia e a hora.')
    desde, ultimo = _limites_cliente(cfg)
    if inicio < desde:
        return _erro('Essa hora já não pode ser marcada — escolhe outra.')
    if inicio.astimezone(fuso()).date() > ultimo:
        return _erro(f'Só se pode marcar até {cfg.dias_max} dias à frente.')
    pagamento = d.get('pagamento') or ('local' if s.pagamento == 'local' else 'antecipado')
    if pagamento not in ('antecipado', 'local') or (s.pagamento != 'ambos' and pagamento != s.pagamento):
        return _erro('Forma de pagamento inválida para este serviço.')
    notas, e = _texto(d, 'notas', 500)
    if e:
        return _erro(e)
    ativas = Marcacao.objects.filter(loja=loja, cliente=u, estado__in=Marcacao.ATIVOS, inicio__gte=timezone.now()).count()
    if ativas >= MAX_ATIVAS_POR_LOJA:
        return _erro(f'Já tens {ativas} marcações nesta loja. Cancela ou espera por uma antes de marcar outra.')
    if not _hora_proposta(s, inicio, prof, desde):
        return _erro('Essa hora já não está livre — escolhe outra.')
    if pagamento == 'antecipado':
        estado, expira = 'pendente', timezone.now() + timedelta(minutes=MINUTOS_PARA_PAGAR)
    else:
        estado, expira = ('confirmada' if cfg.confirmacao == 'auto' else 'pendente'), None
    try:
        m = ops.criar(loja, s, inicio, prof, cliente=u, notas_cliente=notas, estado=estado, pagamento=pagamento,
                      por='', expira_em=expira)
    except ErroMarcacao as e:
        return _erro(str(e))
    if pagamento == 'local':
        ops.avisar_loja(m, 'Nova marcação' if estado == 'confirmada' else 'Nova marcação — confirma-a',
                        f'{m.servico_nome} a {ops.quando_texto(m.inicio)} com {m.profissional.nome} — {u.nome}.', tipo='marcacao_nova')
    m = Marcacao.objects.select_related('loja__config_servicos', 'profissional').get(pk=m.pk)
    return Response(_cliente_payload(request, m, completo=True), status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def minhas(request):
    """GET /app/marcacoes/?tipo=proximas|anteriores"""
    u = request.user.utilizador
    ops.expirar_vencidas(cliente=u)
    qs = Marcacao.objects.filter(cliente=u).select_related('loja__config_servicos', 'profissional')
    agora = timezone.now()
    if request.GET.get('tipo') == 'anteriores':
        qs = qs.filter(Q(fim__lt=agora) | ~Q(estado__in=Marcacao.ATIVOS)).order_by('-inicio')
    else:
        qs = qs.filter(fim__gte=agora, estado__in=Marcacao.ATIVOS).order_by('inicio')
    return Response([_cliente_payload(request, m) for m in qs[:100]])


def _do_cliente(request, mid):
    m = get_object_or_404(Marcacao.objects.select_related('loja__config_servicos', 'profissional', 'cliente__user'), id=mid)
    if m.cliente_id != request.user.utilizador.id:
        return None
    return m


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def minha(request, marcacao_id):
    """GET /app/marcacoes/<id>/ — com a conversa e as propostas."""
    ops.expirar_vencidas(cliente=request.user.utilizador)
    m = _do_cliente(request, marcacao_id)
    if not m:
        return _erro('Marcação não encontrada.', status.HTTP_404_NOT_FOUND)
    conversa.marcar_lida(m, 'cliente')
    return Response(_cliente_payload(request, m, completo=True))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def minha_acao(request, marcacao_id):
    """
    POST /app/marcacoes/<id>/acao/
      { acao: 'pagar' } (simulado) · { acao: 'cancelar', motivo? } · { acao: 'remarcar', inicio }
      { acao: 'aceitar_proposta' | 'recusar_proposta', proposta_id }
    """
    m = _do_cliente(request, marcacao_id)
    if not m:
        return _erro('Marcação não encontrada.', status.HTTP_404_NOT_FOUND)
    d = request.data
    acao = d.get('acao')
    try:
        if acao == 'pagar':
            m = ops.pagar(m)
        elif acao == 'cancelar':
            motivo, e = _texto(d, 'motivo', 200)
            if e:
                return _erro(e)
            m = ops.cancelar_cliente(m, motivo)
        elif acao == 'remarcar':
            if timezone.now() >= m.inicio:
                return _erro('A marcação já começou — já não se remarca.')
            if not ops.dentro_do_prazo(m):
                return _erro(f'Só podes remarcar até {m.loja.config_servicos.cancelar_horas} h antes. Fala com a loja pelas mensagens.')
            if m.pagamento == 'antecipado' and not m.pago:
                return _erro('Paga primeiro a marcação (ou marca outra vez).')
            inicio = _ler_dt(d.get('inicio'))
            if not inicio:
                return _erro('Escolhe o dia e a hora novos.')
            desde, ultimo = _limites_cliente(m.loja.config_servicos)
            if inicio < desde or inicio.astimezone(fuso()).date() > ultimo:
                return _erro('Essa hora não pode ser marcada — escolhe outra.')
            if inicio.minute % 15 or inicio.second:
                return _erro('Escolhe uma das horas propostas.')
            m = ops.remarcar(m, inicio, por='Cliente', pelo_cliente=True)
        elif acao in ('aceitar_proposta', 'recusar_proposta'):
            pid = d.get('proposta_id')
            if isinstance(pid, bool) or not isinstance(pid, int):
                return _erro('Proposta inválida.')
            m = conversa.responder(m, pid, acao == 'aceitar_proposta', request.user.utilizador)
        else:
            return _erro('Acção inválida.')
    except ErroMarcacao as e:
        return _erro(str(e))
    except conversa.ErroConversa as e:
        return _erro(e.mensagem, e.status)
    m = Marcacao.objects.select_related('loja__config_servicos', 'profissional', 'cliente__user').get(pk=m.pk)
    return Response(_cliente_payload(request, m, completo=True))


# ══════════════════════════════════════════════════════════════
# CONVERSA (cliente e loja)
# ══════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@permission_classes([IsAuthenticated])
def mensagens(request, marcacao_id):
    """
    GET  /app/marcacoes/<id>/mensagens/   → {papel, mensagens, propostas, pode_conversar}
    POST /app/marcacoes/<id>/mensagens/   { texto } + fotos (multipart, campo "fotos")
    """
    u = request.user.utilizador
    m = get_object_or_404(Marcacao.objects.select_related('loja', 'profissional__membro', 'cliente__user'), id=marcacao_id)
    papel = conversa.papel(u, m)
    if not papel:
        return _erro('Marcação não encontrada.', status.HTTP_404_NOT_FOUND)
    if request.method == 'POST':
        if is_ratelimited(request=request, group='servicos_mensagem', key='user', rate='60/h', method='POST', increment=True):
            return _erro('Demasiadas mensagens. Tenta mais tarde.', 429)
        ficheiros = request.FILES.getlist('fotos') if hasattr(request, 'FILES') else []
        texto = request.data.get('texto') or ''
        if not isinstance(texto, str):
            return _erro('Mensagem inválida.')
        try:
            conversa.escrever(m, u, papel, texto, ficheiros)
        except conversa.ErroConversa as e:
            return _erro(e.mensagem, e.status)
    else:
        conversa.marcar_lida(m, papel)
    return Response({'papel': papel, 'pode_conversar': conversa.pode_conversar(m),
                     'mensagens': conversa.mensagens_payload(request, m, papel), 'propostas': conversa.propostas_payload(m)},
                    status=status.HTTP_201_CREATED if request.method == 'POST' else status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes([])          # <img src> não envia o token — a autorização vem na assinatura
@permission_classes([AllowAny])
def foto(request, foto_id):
    lido = conversa.ler_assinatura_foto(request.query_params.get('t', ''))
    if not lido or lido[0] != foto_id:
        return Response({'detail': 'Link inválido ou expirado.'}, status=403)
    f = FotoMarcacao.objects.select_related('marcacao').filter(id=foto_id).first()
    u = Utilizador.objects.filter(id=lido[1]).select_related('user').first()
    if not f or not u or not u.user.is_active or not conversa.papel(u, f.marcacao):
        return Response({'detail': 'Foto não encontrada.'}, status=404)
    armazenamento = f.ficheiro.storage
    if hasattr(armazenamento, 'bucket_name'):
        resp = HttpResponseRedirect(armazenamento.url(f.ficheiro.name))
    else:
        resp = FileResponse(armazenamento.open(f.ficheiro.name, 'rb'), content_type='image/webp')
    resp['Cache-Control'] = 'private, max-age=3600'
    resp['X-Content-Type-Options'] = 'nosniff'
    resp['Content-Disposition'] = 'inline'
    return resp
