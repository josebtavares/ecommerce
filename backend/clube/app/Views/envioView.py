"""
Envio por transportadora (utils/envios.py).

GET   /app/transportadoras/                                   lista ativa (formulários da loja)
GET   /app/admin/transportadoras/                             todas (gerir_plataforma)
POST  /app/admin/transportadoras/                             { nome, url_rastreio?, contacto?, ordem? }
PATCH /app/admin/transportadoras/<id>/                        { nome?, url_rastreio?, contacto?, ordem?, ativa? }
POST  /app/loja/<id>/encomendas/<enc>/envio/                  multipart { transportadora_id | transportadora_outra,
                                                                codigos (JSON), talao?, nota? } — enviar / reenviar
POST  /app/loja/<id>/encomendas/<enc>/envio/corrigir/         { transportadora_id | transportadora_outra, codigos, nota? }
POST  /app/loja/<id>/encomendas/<enc>/envio/devolvida/        { nota }
POST  /app/encomenda/<id>/envio/recebi/ · nao-recebi/          o cliente (fase 2)
GET   /app/admin/envios/?filtro=&loja_id=                     envios com problemas (gerir_encomendas, fase 3)
"""
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Encomenda, Loja, Transportadora
from ..utils import envios as E
from ..utils import prova_entrega as P
from .adminView import _exige_admin
from .entregaavaliacaoView import _exige_permissao


def _t(t):
    return {'id': t.id, 'nome': t.nome, 'url_rastreio': t.url_rastreio, 'contacto': t.contacto,
            'ativa': t.ativa, 'ordem': t.ordem}


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def transportadoras(request):
    return Response([_t(t) for t in Transportadora.objects.filter(ativa=True)])


def _dados_transportadora(dados, t=None):
    out = {}
    if 'nome' in dados or t is None:
        nome = ' '.join(str(dados.get('nome') or '').split())
        if len(nome) < 2 or len(nome) > 80:
            raise E.ErroEnvio('O nome tem de ter entre 2 e 80 caracteres.')
        out['nome'] = nome
    if 'url_rastreio' in dados:
        out['url_rastreio'] = E.validar_url(dados.get('url_rastreio'))
    if 'contacto' in dados:
        out['contacto'] = str(dados.get('contacto') or '').strip()[:200]
    if 'ordem' in dados:
        try:
            out['ordem'] = max(0, min(int(dados.get('ordem')), 1000))
        except (TypeError, ValueError):
            raise E.ErroEnvio('Ordem inválida.')
    if 'ativa' in dados and t is not None:
        out['ativa'] = dados.get('ativa') in (True, 'true', '1', 1)
    return out


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def admin_transportadoras(request):
    erro = _exige_admin(request, 'gerir_plataforma')
    if erro:
        return erro
    if request.method == 'GET':
        return Response([_t(t) for t in Transportadora.objects.all()])
    try:
        t = Transportadora.objects.create(**_dados_transportadora(request.data))
    except E.ErroEnvio as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except IntegrityError:
        return Response({'detail': 'Já existe uma transportadora com esse nome.'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(_t(t), status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def admin_transportadora(request, transportadora_id):
    erro = _exige_admin(request, 'gerir_plataforma')
    if erro:
        return erro
    t = get_object_or_404(Transportadora, id=transportadora_id)
    try:
        for k, v in _dados_transportadora(request.data, t).items():
            setattr(t, k, v)
        with transaction.atomic():
            t.save()
    except E.ErroEnvio as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except IntegrityError:
        return Response({'detail': 'Já existe uma transportadora com esse nome.'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(_t(t))


def _membro(request, loja_id):
    loja = get_object_or_404(Loja, id=loja_id)
    membro, erro = _exige_permissao(request, loja, 'gerir_encomendas')
    if erro:
        return loja, None, erro
    if not membro.pk:            # admin a ver o backoffice só para leitura
        return loja, None, Response({'detail': 'Só de leitura.'}, status=status.HTTP_403_FORBIDDEN)
    return loja, membro, None


def _resposta(encomenda, request):
    encomenda.refresh_from_db()
    ent = encomenda.entrega
    return Response({'encomenda_id': encomenda.id, 'status': encomenda.status,
                     'envio': E.dados(ent, request, loja=True)})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enviar(request, loja_id, encomenda_id):
    loja, membro, erro = _membro(request, loja_id)
    if erro:
        return erro
    # verificação barata antes de converter a foto do talão
    previa = get_object_or_404(Encomenda, id=encomenda_id, loja=loja)
    msg = E.pode_enviar(previa)
    if msg:
        return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)
    try:
        talao = P.preparar(request.FILES.get('talao'))
    except P.ErroProva as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    d = request.data
    try:
        with transaction.atomic():
            enc = get_object_or_404(Encomenda.objects.select_for_update(of=('self',)), id=encomenda_id, loja=loja)
            E.enviar(enc, request.user.utilizador, d.get('transportadora_id'), d.get('transportadora_outra', ''),
                     d.get('codigos'), talao, d.get('nota', ''))
    except E.ErroEnvio as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return _resposta(enc, request)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def corrigir(request, loja_id, encomenda_id):
    loja, membro, erro = _membro(request, loja_id)
    if erro:
        return erro
    d = request.data
    try:
        with transaction.atomic():
            enc = get_object_or_404(Encomenda.objects.select_for_update(of=('self',)), id=encomenda_id, loja=loja)
            E.corrigir(enc, request.user.utilizador, d.get('transportadora_id'), d.get('transportadora_outra', ''),
                       d.get('codigos'), d.get('nota', ''))
    except E.ErroEnvio as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return _resposta(enc, request)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def devolvida(request, loja_id, encomenda_id):
    loja, membro, erro = _membro(request, loja_id)
    if erro:
        return erro
    try:
        with transaction.atomic():
            enc = get_object_or_404(Encomenda.objects.select_for_update(of=('self',)), id=encomenda_id, loja=loja)
            E.devolvida(enc, request.user.utilizador, request.data.get('nota', ''))
    except E.ErroEnvio as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return _resposta(enc, request)


# ── cliente ────────────────────────────────────────────────────────────────────
# POST /app/encomenda/<id>/envio/recebi/       → conclui (prazo de devolução começa agora)
# POST /app/encomenda/<id>/envio/nao-recebi/   { nota? } → avisa a loja; o fecho automático fica parado

def _do_cliente(request, encomenda_id):
    return get_object_or_404(Encomenda.objects.select_for_update(of=('self',)), id=encomenda_id,
                             comprador=request.user.utilizador)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cliente_recebi(request, encomenda_id):
    try:
        with transaction.atomic():
            enc = _do_cliente(request, encomenda_id)
            E.concluir(enc, por='cliente')
    except E.ErroEnvio as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'encomenda_id': enc.id, 'status': enc.status})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cliente_nao_recebi(request, encomenda_id):
    nota = request.data.get('nota') or ''
    if not isinstance(nota, str):
        return Response({'detail': 'Nota inválida.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        with transaction.atomic():
            enc = _do_cliente(request, encomenda_id)
            E.nao_recebi(enc, nota)
    except E.ErroEnvio as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'encomenda_id': enc.id, 'status': enc.status})


# ── admin: envios com problemas ────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_envios(request):
    erro = _exige_admin(request, 'gerir_encomendas')
    if erro:
        return erro
    loja_id = request.GET.get('loja_id') or None
    if loja_id and not str(loja_id).isdigit():
        return Response({'detail': 'Loja inválida.'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(E.problemas(request.GET.get('filtro') or 'problemas', loja_id))
