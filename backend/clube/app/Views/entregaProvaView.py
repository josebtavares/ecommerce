"""
Prova de entrega (utils/prova_entrega.py) e resumo do dia (utils/resumo_entregas.py).

POST /app/loja/<id>/encomendas/<enc>/entrega/prova/   multipart {foto?, assinatura?, recebido_por?} — opcional
GET  /app/entregas/<id>/prova/<foto|assinatura>/?t=    imagem privada (link assinado, 1 h)
GET  /app/loja/<id>/entrega/resumo-dia/?data=AAAA-MM-DD   loja: todos os condutores; condutor: só o seu
"""
from datetime import date, timedelta

from django.db import transaction
from django.http import FileResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from ..models import Condutor, Encomenda, Entrega, Loja, Utilizador
from ..Serializers.EntregaAvaliacaoSerializer import EntregaSerializer
from ..utils import prova_entrega as P
from ..utils import resumo_entregas as R
from .entregaavaliacaoView import _entrega_do_membro, _exige_permissao


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def prova_juntar(request, loja_id, encomenda_id):
    loja = get_object_or_404(Loja, id=loja_id)
    membro, erro = _exige_permissao(request, loja, 'gerir_entregas')
    if erro:
        return erro
    if not membro.pk:
        return Response({'detail': 'Só de leitura.'}, status=status.HTTP_403_FORBIDDEN)
    nome = request.data.get('recebido_por') or ''
    if not isinstance(nome, str):
        return Response({'detail': 'Nome inválido.'}, status=status.HTTP_400_BAD_REQUEST)
    # verificação barata primeiro: não se convertem imagens de quem não pode juntar prova a esta entrega
    previa = Entrega.objects.select_related('condutor').filter(encomenda_id=encomenda_id, encomenda__loja=loja).first()
    if not previa:
        return Response({'detail': 'Entrega não encontrada.'}, status=status.HTTP_404_NOT_FOUND)
    if not _entrega_do_membro(membro, previa):
        return Response({'detail': 'Esta entrega não é tua.'}, status=status.HTTP_403_FORBIDDEN)
    try:
        # converter as imagens é lento: antes de bloquear a entrega
        foto = P.preparar(request.FILES.get('foto'))
        assinatura = P.preparar(request.FILES.get('assinatura'))
        with transaction.atomic():
            encomenda = get_object_or_404(Encomenda, id=encomenda_id, loja=loja)
            entrega = get_object_or_404(Entrega.objects.select_for_update(of=('self',))
                                        .select_related('condutor'), encomenda=encomenda)
            if not _entrega_do_membro(membro, entrega):
                return Response({'detail': 'Esta entrega não é tua.'}, status=status.HTTP_403_FORBIDDEN)
            P.gravar(entrega, foto, assinatura, nome)
    except P.ErroProva as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    from ..utils.tempo_real_encomendas import emitir
    transaction.on_commit(lambda: emitir(encomenda.id))
    return Response(EntregaSerializer(entrega, context={'request': request}).data)


@api_view(['GET'])
@authentication_classes([])          # <img src> não envia o token — a autorização vem na assinatura
@permission_classes([AllowAny])
def prova_ficheiro(request, entrega_id, parte):
    lido = P.ler(request.query_params.get('t', ''))
    if not lido or lido[0] != entrega_id or lido[1] != parte:
        return Response({'detail': 'Link inválido ou expirado.'}, status=403)
    e = Entrega.objects.select_related('encomenda__loja', 'condutor').filter(id=entrega_id).first()
    u = Utilizador.objects.filter(id=lido[2]).select_related('user').first()
    f = getattr(e, f'prova_{parte}', None) if e else None
    # o acesso volta a ser verificado: quem saiu da loja deixa de ver, mesmo com o link
    pode = u and u.user.is_active and (P.pode_ver(u, e) or (lido[3] and u.user.is_staff))
    if not f or not pode:
        return Response({'detail': 'Imagem não encontrada.'}, status=404)
    armazenamento = f.storage
    if hasattr(armazenamento, 'bucket_name'):
        resp = HttpResponseRedirect(armazenamento.url(f.name))
    else:
        resp = FileResponse(armazenamento.open(f.name, 'rb'), content_type='image/webp')
    resp['Cache-Control'] = 'private, max-age=3600'
    resp['X-Content-Type-Options'] = 'nosniff'
    resp['Content-Disposition'] = 'inline'
    return resp


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def resumo_dia(request, loja_id):
    loja = get_object_or_404(Loja, id=loja_id)
    membro, erro = _exige_permissao(request, loja, 'gerir_entregas')
    if erro:
        return erro
    hoje = timezone.localdate()
    texto = request.query_params.get('data') or ''
    try:
        dia = date.fromisoformat(texto) if texto else hoje
    except ValueError:
        return Response({'detail': 'Data inválida.'}, status=status.HTTP_400_BAD_REQUEST)
    if dia > hoje or dia < hoje - timedelta(days=R.DIAS_MAX):
        return Response({'detail': 'Escolhe um dia até hoje (máx. 1 ano para trás).'},
                        status=status.HTTP_400_BAD_REQUEST)
    condutor = None
    if membro.role == 'condutor':
        condutor = Condutor.objects.filter(loja=loja, utilizador=membro.utilizador, ativo=True).first()
        if not condutor:
            return Response({'detail': 'Não és condutor desta loja.'}, status=status.HTTP_403_FORBIDDEN)
    return Response(R.do_dia(loja, dia, condutor))
