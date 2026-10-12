"""
API do chat — /api/chat/…  (as regras estão em regras.py)

Cada pedido diz "como quem" age através de `caixa` (id de uma Caixa a que o utilizador tem acesso).
"""
from django.db.models import Count, Q, Max
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_ratelimit.core import is_ratelimited
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from app.models import Loja, Produto, Utilizador, UtilizadorLoja, Encomenda

from django.http import FileResponse, HttpResponseRedirect
from rest_framework.decorators import authentication_classes
from rest_framework.permissions import AllowAny

from . import regras, imagens
from .models import Caixa, Conversa, Participante, Mensagem, Bloqueio, Denuncia
from .regras import ErroChat
from .tempo_real import emitir

TEXTO_MAX = 4000


def url_ficheiro(request, ficheiro):
    """URL absoluto de um ficheiro (media/ na dev, R2 na prod)."""
    try:
        return request.build_absolute_uri(ficheiro.url)
    except Exception:
        return None


def _erro(e):
    return Response({'detail': e.mensagem}, status=e.status)


def _limitado(request, grupo, taxa):
    return is_ratelimited(request=request, group=f'chat_{grupo}', key='user', rate=taxa,
                          method=request.method, increment=True)


def _demasiados():
    return Response({'detail': 'Estás a enviar demasiado depressa. Aguarda um momento.'},
                    status=status.HTTP_429_TOO_MANY_REQUESTS)


def _caixa_do_pedido(request, valor):
    """A caixa pedida (id), se o utilizador tiver acesso a ela."""
    try:
        caixa = Caixa.objects.select_related('loja', 'utilizador__user').get(id=int(valor))
    except (TypeError, ValueError, Caixa.DoesNotExist):
        raise ErroChat('Caixa inválida.', 400)
    if regras.acesso_caixa(request.user.utilizador, caixa) is None:
        raise ErroChat('Sem acesso a esta caixa.', 403)
    return caixa


# ══════════════════════════════════════════════════════════════
# Apresentação
# ══════════════════════════════════════════════════════════════

def _foto_utilizador(request, u):
    return url_ficheiro(request, u.foto) if u and u.foto else None


def perfil_caixa(request, caixa):
    """Como uma caixa aparece aos outros: nome, foto e tipo."""
    if caixa is None:
        return {'caixa_id': None, 'tipo': None, 'nome': 'Conta removida', 'foto': None}
    if caixa.tipo == Caixa.PESSOAL:
        u = caixa.utilizador
        return {'caixa_id': caixa.id, 'tipo': 'pessoal', 'utilizador_id': u.id, 'nome': u.nome,
                'foto': _foto_utilizador(request, u)}
    if caixa.tipo == Caixa.LOJA:
        loja = caixa.loja
        return {'caixa_id': caixa.id, 'tipo': 'loja', 'loja_id': loja.id, 'nome': loja.nome,
                'foto': url_ficheiro(request, loja.logo) if loja.logo else None}
    return {'caixa_id': caixa.id, 'tipo': 'suporte', 'nome': 'Suporte Bendi', 'foto': None}


def _produto_cartao(request, p):
    if not p:
        return None
    img = p.ficheiro_poster or p.ficheiro
    return {'id': p.id, 'nome': p.nome, 'preco': str(p.preco), 'loja_id': p.loja_id,
            'imagem': url_ficheiro(request, img) if img else None}


def _anexo_payload(request, m):
    """Imagem privada: link assinado para quem está a pedir (válido 1h — ver imagens.py)."""
    if m.apagada or m.tipo != Mensagem.IMAGEM or not m.anexo:
        return None
    token = imagens.assinar(m.id, request.user.utilizador.id)
    return {
        'url': request.build_absolute_uri(f'/api/chat/anexos/{m.id}/?t={token}'),
        'largura': m.anexo_largura,
        'altura': m.anexo_altura,
    }


def mensagem_payload(request, m, caixa_vista, leitura_outros=0):
    """`caixa_vista`: a caixa de quem está a ver. `leitura_outros`: maior ultima_lida das outras caixas."""
    minha = m.remetente_id == caixa_vista.id
    dados = {
        'id': m.id,
        'conversa_id': m.conversa_id,
        'tipo': m.tipo,
        'texto': '' if m.apagada else m.texto,
        'apagada': m.apagada,
        'criada_em': m.criada_em.isoformat(),
        'minha': minha,
        'remetente': perfil_caixa(request, m.remetente),
        'produto': None if m.apagada else _produto_cartao(request, m.produto),
        'anexo': _anexo_payload(request, m),
        'lida': minha and leitura_outros >= m.id,
    }
    # quem escreveu de facto: só para quem partilha a caixa (a equipa vê "respondido por João")
    if m.autor_id and m.remetente_id == caixa_vista.id and caixa_vista.tipo != Caixa.PESSOAL:
        dados['autor'] = {'utilizador_id': m.autor_id, 'nome': m.autor.nome}
    return dados


def _titulo_e_outro(request, conversa, caixa_vista):
    if conversa.tipo == Conversa.EQUIPA_GRUPO:
        return f'Equipa · {conversa.loja.nome}', {
            'caixa_id': None, 'tipo': 'equipa', 'loja_id': conversa.loja_id, 'nome': f'Equipa · {conversa.loja.nome}',
            'foto': url_ficheiro(request, conversa.loja.logo) if conversa.loja.logo else None}
    outras = [p.caixa for p in conversa.participantes.all() if p.caixa_id != caixa_vista.id]
    outro = perfil_caixa(request, outras[0]) if outras else perfil_caixa(request, None)
    return outro['nome'], outro


def conversa_payload(request, conversa, caixa_vista):
    titulo, outro = _titulo_e_outro(request, conversa, caixa_vista)
    eu = next((p for p in conversa.participantes.all() if p.caixa_id == caixa_vista.id), None)
    lida = eu.ultima_lida if eu else 0
    ultima = conversa.mensagens.select_related('remetente__loja', 'remetente__utilizador__user', 'produto', 'autor__user') \
        .order_by('-id').first()
    nao_lidas = conversa.mensagens.filter(id__gt=lida, apagada=False).exclude(remetente=caixa_vista).count()
    leitura_outros = max([p.ultima_lida for p in conversa.participantes.all() if p.caixa_id != caixa_vista.id] or [0])
    return {
        'id': conversa.id,
        'tipo': conversa.tipo,
        'titulo': titulo,
        'outro': outro,
        'assunto': conversa.assunto,
        'estado': conversa.estado,
        'loja_id': conversa.loja_id,
        'encomenda_id': conversa.encomenda_id,
        'caixa_id': caixa_vista.id,
        'ultima_mensagem': mensagem_payload(request, ultima, caixa_vista, leitura_outros) if ultima else None,
        'ultima_mensagem_em': conversa.ultima_mensagem_em.isoformat() if conversa.ultima_mensagem_em else None,
        'nao_lidas': nao_lidas,
        'silenciada': bool(eu and eu.silenciada),
        'arquivada': bool(eu and eu.arquivada),
    }


def _qs_conversas():
    return Conversa.objects.select_related('loja').prefetch_related(
        'participantes__caixa__loja', 'participantes__caixa__utilizador__user')


# ══════════════════════════════════════════════════════════════
# Caixas
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def caixas(request):
    """GET /api/chat/caixas/ — as caixas a que tenho acesso, com não lidas."""
    u = request.user.utilizador
    regras.sincronizar_grupos(u)
    out = []
    for caixa, restrita in regras.caixas_de(u):
        nao_lidas = 0
        for conv in regras.conversas_visiveis(u, caixa).prefetch_related('participantes'):
            eu = next((p for p in conv.participantes.all() if p.caixa_id == caixa.id), None)
            nao_lidas += conv.mensagens.filter(id__gt=eu.ultima_lida if eu else 0, apagada=False) \
                .exclude(remetente=caixa).count()
        out.append({**perfil_caixa(request, caixa), 'restrita': restrita, 'nao_lidas': nao_lidas})
    return Response(out)


# ══════════════════════════════════════════════════════════════
# Conversas
# ══════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def conversas(request):
    """
    GET  /api/chat/conversas/?caixa=<id>&tipo=&q=&arquivadas=0&offset=&limit=
    POST /api/chat/conversas/  { caixa, destino: loja|utilizador|suporte|equipa_grupo,
                                  destino_id?, encomenda_id?, loja_id? }  → abre ou devolve a existente
    """
    u = request.user.utilizador
    try:
        if request.method == 'POST':
            if _limitado(request, 'iniciar', '20/h'):
                return _demasiados()
            caixa = _caixa_do_pedido(request, request.data.get('caixa'))
            conv = regras.iniciar(u, caixa, request.data.get('destino'),
                                  destino_id=request.data.get('destino_id'),
                                  encomenda_id=request.data.get('encomenda_id'),
                                  loja_id=request.data.get('loja_id'))
            # no grupo da equipa a caixa é sempre a pessoal
            if conv.tipo == Conversa.EQUIPA_GRUPO:
                caixa = Caixa.de_utilizador(u)
            conv = _qs_conversas().get(id=conv.id)
            return Response(conversa_payload(request, conv, caixa), status=status.HTTP_200_OK)

        caixa = _caixa_do_pedido(request, request.query_params.get('caixa'))
        qs = regras.conversas_visiveis(u, caixa)
        tipo = request.query_params.get('tipo')
        if tipo:
            qs = qs.filter(tipo=tipo)
        arquivadas = request.query_params.get('arquivadas') == '1'
        qs = qs.filter(**({'participantes__caixa': caixa, 'participantes__arquivada': True} if arquivadas else {})) \
            if arquivadas else qs.exclude(participantes__caixa=caixa, participantes__arquivada=True)
        q = (request.query_params.get('q') or '').strip()
        if q:
            qs = qs.filter(
                Q(assunto__icontains=q) | Q(loja__nome__icontains=q)
                | Q(participantes__caixa__utilizador__user__username__icontains=q)
                | Q(participantes__caixa__utilizador__user__first_name__icontains=q)
                | Q(participantes__caixa__utilizador__user__last_name__icontains=q)
                | Q(participantes__caixa__loja__nome__icontains=q)
            ).distinct()
        try:
            offset = max(int(request.query_params.get('offset', 0)), 0)
            limit = min(max(int(request.query_params.get('limit', 30)), 1), 50)
        except ValueError:
            return Response({'detail': 'offset/limit inválidos.'}, status=400)
        total = qs.count()
        lista = _qs_conversas().filter(id__in=qs.values('id')).order_by(
            '-ultima_mensagem_em', '-id')[offset:offset + limit]
        return Response({
            'count': total,
            'next_offset': offset + limit if offset + limit < total else None,
            'results': [conversa_payload(request, c, caixa) for c in lista],
        })
    except ErroChat as e:
        return _erro(e)


def _conversa_e_caixa(request, conversa_id, caixa_id):
    u = request.user.utilizador
    conversa = get_object_or_404(_qs_conversas(), id=conversa_id)
    caixa = _caixa_do_pedido(request, caixa_id)
    if not regras.pode_usar(u, conversa, caixa):
        raise ErroChat('Sem acesso a esta conversa.', 404)
    return conversa, caixa


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def conversa_detalhe(request, conversa_id):
    """GET /api/chat/conversas/<id>/?caixa=<id>"""
    try:
        conversa, caixa = _conversa_e_caixa(request, conversa_id, request.query_params.get('caixa'))
        return Response(conversa_payload(request, conversa, caixa))
    except ErroChat as e:
        return _erro(e)


# ══════════════════════════════════════════════════════════════
# Mensagens
# ══════════════════════════════════════════════════════════════

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def mensagens(request, conversa_id):
    """
    GET  /api/chat/conversas/<id>/mensagens/?caixa=<id>&antes=<msg id>&limit=
    POST /api/chat/conversas/<id>/mensagens/  { caixa, texto, produto_id? }
    """
    u = request.user.utilizador
    caixa_id = request.data.get('caixa') if request.method == 'POST' else request.query_params.get('caixa')
    try:
        conversa, caixa = _conversa_e_caixa(request, conversa_id, caixa_id)

        if request.method == 'POST':
            if _limitado(request, 'enviar', '30/m'):
                return _demasiados()
            regras.verificar_envio(u, conversa, caixa)
            texto = (request.data.get('texto') or '').strip()
            ficheiro = request.FILES.get('imagem')
            if not texto and not ficheiro:
                return Response({'detail': 'A mensagem está vazia.'}, status=400)
            if len(texto) > TEXTO_MAX:
                return Response({'detail': f'Máximo de {TEXTO_MAX} caracteres.'}, status=400)

            imagem = None
            if ficheiro:
                if not imagens.imagens_disponiveis():
                    return Response({'detail': 'O envio de imagens ainda não está disponível.'}, status=503)
                if _limitado(request, 'imagens', '40/h'):
                    return _demasiados()
                try:
                    imagem = imagens.processar(ficheiro)     # (ContentFile webp, largura, altura)
                except imagens.ImagemInvalida as e:
                    return Response({'detail': str(e)}, status=400)
            produto = None
            if request.data.get('produto_id'):
                # o cartão de produto só pode ser da loja desta conversa, e de uma loja visível
                produto = Produto.objects.filter(id=request.data.get('produto_id'), ativo=True,
                                                 loja_id=conversa.loja_id, loja__ativa=True).first()
                if not produto:
                    return Response({'detail': 'Produto inválido para esta conversa.'}, status=400)
            m = Mensagem(conversa=conversa, remetente=caixa, autor=u, texto=texto, produto=produto)
            if imagem:
                conteudo, m.anexo_largura, m.anexo_altura = imagem
                m.tipo = Mensagem.IMAGEM
                m.anexo.save(conteudo.name, conteudo, save=False)
            m.save()
            regras.registar_envio(conversa, caixa, m)
            emitir(conversa, {'tipo': 'mensagem_nova', 'conversa_id': conversa.id, 'mensagem_id': m.id})
            return Response(mensagem_payload(request, m, caixa), status=status.HTTP_201_CREATED)

        try:
            limit = min(max(int(request.query_params.get('limit', 40)), 1), 100)
            antes = int(request.query_params.get('antes') or 0)
            depois = int(request.query_params.get('depois') or 0)
        except ValueError:
            return Response({'detail': 'Parâmetros inválidos.'}, status=400)
        qs = conversa.mensagens.select_related('remetente__loja', 'remetente__utilizador__user',
                                               'produto', 'autor__user')
        if depois:
            # só as novas (o WebSocket avisa e o browser vem buscar as que faltam)
            pagina = list(qs.filter(id__gt=depois).order_by('id')[:limit])
            mais = False
        else:
            if antes:
                qs = qs.filter(id__lt=antes)
            pagina = list(qs.order_by('-id')[:limit + 1])
            mais = len(pagina) > limit
            pagina = list(reversed(pagina[:limit]))
        leitura_outros = conversa.participantes.exclude(caixa=caixa).aggregate(m=Max('ultima_lida'))['m'] or 0
        return Response({
            'results': [mensagem_payload(request, m, caixa, leitura_outros) for m in pagina],
            'mais_antigas': mais,
        })
    except ErroChat as e:
        return _erro(e)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def marcar_lida(request, conversa_id):
    """POST /api/chat/conversas/<id>/lida/ { caixa, ate? } — sem `ate`, marca tudo."""
    try:
        conversa, caixa = _conversa_e_caixa(request, conversa_id, request.data.get('caixa'))
        ultima = conversa.mensagens.aggregate(m=Max('id'))['m'] or 0
        try:
            ate = min(int(request.data.get('ate') or ultima), ultima)
        except ValueError:
            return Response({'detail': 'Parâmetro inválido.'}, status=400)
        p, _ = Participante.objects.get_or_create(conversa=conversa, caixa=caixa)
        if ate > p.ultima_lida:
            p.ultima_lida = ate
            p.save(update_fields=['ultima_lida'])
            # ✓✓ para quem enviou (e o contador desce noutros separadores de quem leu)
            emitir(conversa, {'tipo': 'lida', 'conversa_id': conversa.id, 'caixa_id': caixa.id,
                              'ultima_lida': p.ultima_lida})
        return Response({'ultima_lida': p.ultima_lida})
    except ErroChat as e:
        return _erro(e)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def preferencias(request, conversa_id):
    """POST /api/chat/conversas/<id>/preferencias/ { caixa, silenciada?, arquivada? }"""
    try:
        conversa, caixa = _conversa_e_caixa(request, conversa_id, request.data.get('caixa'))
        p, _ = Participante.objects.get_or_create(conversa=conversa, caixa=caixa)
        for campo in ('silenciada', 'arquivada'):
            if campo in request.data:
                setattr(p, campo, str(request.data.get(campo)).lower() in ('1', 'true'))
        p.save(update_fields=['silenciada', 'arquivada'])
        return Response({'silenciada': p.silenciada, 'arquivada': p.arquivada})
    except ErroChat as e:
        return _erro(e)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def estado_conversa(request, conversa_id):
    """POST /api/chat/conversas/<id>/estado/ { caixa, estado: aberta|fechada } — só o suporte."""
    try:
        conversa, caixa = _conversa_e_caixa(request, conversa_id, request.data.get('caixa'))
        if conversa.tipo != Conversa.SUPORTE or caixa.tipo != Caixa.SUPORTE:
            return Response({'detail': 'Só o suporte fecha ou reabre pedidos.'}, status=403)
        novo = request.data.get('estado')
        if novo not in (Conversa.ABERTA, Conversa.FECHADA):
            return Response({'detail': 'Estado inválido.'}, status=400)
        conversa.estado = novo
        conversa.save(update_fields=['estado'])
        emitir(conversa, {'tipo': 'conversa_atualizada', 'conversa_id': conversa.id})
        return Response({'estado': conversa.estado})
    except ErroChat as e:
        return _erro(e)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apagar_mensagem(request, mensagem_id):
    """POST /api/chat/mensagens/<id>/apagar/ — só quem a escreveu ("Mensagem apagada")."""
    m = get_object_or_404(Mensagem.objects.select_related('conversa'), id=mensagem_id)
    if m.autor_id != request.user.utilizador.id or m.tipo == Mensagem.SISTEMA:
        return Response({'detail': 'Só podes apagar as tuas mensagens.'}, status=403)
    if not m.apagada:
        if m.anexo:
            m.anexo.delete(save=False)      # a imagem sai mesmo do armazenamento
        m.apagada = True
        m.texto = ''
        m.save(update_fields=['apagada', 'texto', 'anexo'])
        emitir(m.conversa, {'tipo': 'mensagem_apagada', 'conversa_id': m.conversa_id, 'mensagem_id': m.id})
    return Response({'id': m.id, 'apagada': True})


@api_view(['GET'])
@authentication_classes([])          # <img src> não envia o token — a autorização vem na assinatura
@permission_classes([AllowAny])
def anexo(request, mensagem_id):
    """
    GET /api/chat/anexos/<id>/?t=<assinatura>
    O link é gerado para um utilizador e dura 1h; o acesso à conversa volta a ser verificado aqui
    (quem saiu da loja ou da conversa deixa de abrir a imagem, mesmo com o link).
    """
    lido = imagens.ler_assinatura(request.query_params.get('t', ''))
    if not lido or lido[0] != mensagem_id:
        return Response({'detail': 'Link inválido ou expirado.'}, status=403)
    m = Mensagem.objects.select_related('conversa').filter(id=mensagem_id, apagada=False,
                                                           tipo=Mensagem.IMAGEM).first()
    utilizador = Utilizador.objects.filter(id=lido[1]).select_related('user').first()
    if not m or not m.anexo or not utilizador or not utilizador.is_active:
        return Response({'detail': 'Imagem não encontrada.'}, status=404)
    if not regras.utilizador_ve_conversa(utilizador, m.conversa):
        return Response({'detail': 'Imagem não encontrada.'}, status=404)

    armazenamento = m.anexo.storage
    if hasattr(armazenamento, 'bucket_name'):
        # R2 privado: link temporário (5 min) assinado pelo próprio R2
        resp = HttpResponseRedirect(armazenamento.url(m.anexo.name))
    else:
        resp = FileResponse(armazenamento.open(m.anexo.name, 'rb'), content_type='image/webp')
    resp['Cache-Control'] = 'private, max-age=3600'
    resp['X-Content-Type-Options'] = 'nosniff'
    resp['Content-Disposition'] = 'inline'
    return resp


# ══════════════════════════════════════════════════════════════
# Contactos (com quem posso iniciar conversa)
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def contactos(request):
    """
    GET /api/chat/contactos/?caixa=<id>&q=&tipo=loja|cliente|equipa|dono|staff|admin
    Só devolve quem esta caixa pode contactar (mínimo 2 letras).
    """
    u = request.user.utilizador
    try:
        caixa = _caixa_do_pedido(request, request.query_params.get('caixa'))
        if regras.acesso_caixa(u, caixa) != 'total':
            raise ErroChat('Sem acesso a esta caixa.', 403)
    except ErroChat as e:
        return _erro(e)
    q = (request.query_params.get('q') or '').strip()
    tipo = request.query_params.get('tipo') or ''
    if len(q) < 2:
        return Response({'results': []})

    def utilizadores(qs, papel):
        qs = qs.filter(Q(user__username__icontains=q) | Q(user__first_name__icontains=q)
                       | Q(user__last_name__icontains=q), status='ativo').exclude(id=u.id).select_related('user')[:20]
        return [{'tipo': 'utilizador', 'id': x.id, 'nome': x.nome, 'username': x.user.username,
                 'foto': _foto_utilizador(request, x), 'papel': papel} for x in qs]

    def lojas(qs):
        return [{'tipo': 'loja', 'id': l.id, 'nome': l.nome, 'foto': url_ficheiro(request, l.logo) if l.logo else None}
                for l in qs.filter(nome__icontains=q)[:20]]

    out = []
    if caixa.tipo == Caixa.PESSOAL:
        if tipo in ('', 'loja'):
            out += lojas(Loja.objects.filter(estado='ativa', ativa=True))
        if tipo in ('', 'equipa'):
            minhas = UtilizadorLoja.objects.filter(utilizador=u, ativo=True).values('loja_id')
            colegas = Utilizador.objects.filter(lojas_staff__loja_id__in=minhas, lojas_staff__ativo=True).distinct()
            out += utilizadores(colegas, 'equipa')
    elif caixa.tipo == Caixa.LOJA:
        if tipo in ('', 'cliente'):
            clientes = Utilizador.objects.filter(
                Q(encomendas__loja=caixa.loja)
                | Q(caixa_chat__participacoes__conversa__chave__startswith='cl:',
                    caixa_chat__participacoes__conversa__loja=caixa.loja)
            ).exclude(lojas_staff__loja=caixa.loja, lojas_staff__ativo=True).distinct()
            out += utilizadores(clientes, 'cliente')
    else:  # suporte: toda a gente, com filtro por tipo
        if tipo in ('', 'loja'):
            out += lojas(Loja.objects.all())
        base = Utilizador.objects.all()
        filtros = {
            'dono': Q(lojas_staff__role='dono', lojas_staff__ativo=True),
            'staff': Q(lojas_staff__ativo=True) & ~Q(lojas_staff__role='dono'),
            'admin': Q(user__is_staff=True),
            'cliente': ~Q(lojas_staff__ativo=True) & Q(user__is_staff=False),
        }
        if tipo in filtros:
            out += utilizadores(base.filter(filtros[tipo]).distinct(), tipo)
        elif tipo == '':
            out += utilizadores(base, 'utilizador')
    return Response({'results': out})


# ══════════════════════════════════════════════════════════════
# Bloqueios e denúncias
# ══════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bloquear(request, conversa_id):
    """POST /api/chat/conversas/<id>/bloquear/ { caixa, bloquear: true|false } — bloqueia o outro lado."""
    try:
        conversa, caixa = _conversa_e_caixa(request, conversa_id, request.data.get('caixa'))
        if conversa.tipo == Conversa.EQUIPA_GRUPO:
            return Response({'detail': 'Não se bloqueia o grupo da equipa.'}, status=400)
        if regras.acesso_caixa(request.user.utilizador, caixa) != 'total':
            return Response({'detail': 'Sem permissão.'}, status=403)
        outras = regras.outras_caixas(conversa, caixa)
        if any(o.tipo == Caixa.SUPORTE for o in outras):
            return Response({'detail': 'Não é possível bloquear o suporte.'}, status=400)
        quer = str(request.data.get('bloquear', 'true')).lower() in ('1', 'true')
        for o in outras:
            if quer:
                Bloqueio.objects.get_or_create(caixa=caixa, bloqueada=o)
            else:
                Bloqueio.objects.filter(caixa=caixa, bloqueada=o).delete()
        return Response({'bloqueado': quer})
    except ErroChat as e:
        return _erro(e)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def denuncias(request):
    """
    POST /api/chat/denuncias/ { caixa, conversa_id, mensagem_id?, motivo } — qualquer participante
    GET  /api/chat/denuncias/?estado=pendente                            — só moderar_chat
    """
    u = request.user.utilizador
    if request.method == 'POST':
        if _limitado(request, 'denunciar', '10/h'):
            return _demasiados()
        try:
            conversa, caixa = _conversa_e_caixa(request, request.data.get('conversa_id'), request.data.get('caixa'))
        except ErroChat as e:
            return _erro(e)
        motivo = (request.data.get('motivo') or '').strip()[:500]
        if not motivo:
            return Response({'detail': 'Indica o motivo.'}, status=400)
        mensagem = None
        if request.data.get('mensagem_id'):
            mensagem = conversa.mensagens.filter(id=request.data.get('mensagem_id')).first()
            if not mensagem:
                return Response({'detail': 'Mensagem inválida.'}, status=400)
        d = Denuncia.objects.create(conversa=conversa, mensagem=mensagem, denunciante=u, motivo=motivo)
        return Response({'id': d.id, 'estado': d.estado}, status=status.HTTP_201_CREATED)

    if not (request.user.is_staff and u.pode_admin('moderar_chat')):
        return Response({'detail': 'Sem permissão.'}, status=403)
    qs = Denuncia.objects.select_related('denunciante__user', 'mensagem').filter(
        estado=request.query_params.get('estado', Denuncia.PENDENTE))[:100]
    return Response({'results': [{
        'id': d.id, 'conversa_id': d.conversa_id, 'mensagem_id': d.mensagem_id,
        'mensagem_texto': d.mensagem.texto if d.mensagem else None,
        'denunciante': d.denunciante.nome if d.denunciante else None,
        'motivo': d.motivo, 'estado': d.estado, 'criada_em': d.criada_em.isoformat(),
    } for d in qs]})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolver_denuncia(request, denuncia_id):
    """POST /api/chat/denuncias/<id>/resolver/ { nota? } — só moderar_chat."""
    u = request.user.utilizador
    if not (request.user.is_staff and u.pode_admin('moderar_chat')):
        return Response({'detail': 'Sem permissão.'}, status=403)
    d = get_object_or_404(Denuncia, id=denuncia_id)
    d.estado = Denuncia.RESOLVIDA
    d.resolvida_por = u
    d.resolvida_em = timezone.now()
    d.nota = (request.data.get('nota') or '')[:500]
    d.save(update_fields=['estado', 'resolvida_por', 'resolvida_em', 'nota'])
    return Response({'id': d.id, 'estado': d.estado})
