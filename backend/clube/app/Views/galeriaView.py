from django.shortcuts import render
from django.http import JsonResponse
from ..models import Galeria, Utilizador
from ..Serializers.GaleriaSerializer import GaleriaSerializer

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny

@api_view(['GET'])
def galeria_list(request):
    if request.method == 'GET':
        galerias = Galeria.objects.all()
        serializer = GaleriaSerializer(galerias, many=True)
        return JsonResponse(serializer.data, safe=False)


@api_view(['GET'])
def galeria_get(request, id):
    try:
        galeria_ = Galeria.objects.get(id= id)
    except Galeria.DoesNotExist:
        return Response(status=status.HTTP_208_ALREADY_REPORTED)
        
    if request.method == 'GET':
        serializer = GaleriaSerializer(galeria_)
        return JsonResponse(serializer.data, safe=False)
  
    
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([AllowAny])
def galeria_create(request):
    with transaction.atomic():
        # 1) valida e guarda a Galeria
        serializer = GaleriaSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        galeria = serializer.save()

        # 2) interpreta o flag vindo do FormData (string → bool)
        flag = request.data.get('postar_na_feed', 'false').lower()
        postar_na_feed = flag in ('true', '1', 'on')

        # 3) só cria Postagem se o flag for True
        if postar_na_feed:
            post_data = {
                'titulo'       : galeria.titulo,
                'descricao'    : galeria.descricao,
                'ficheiro'     : galeria.ficheiro,
                'utilizador_id': galeria.utilizador.id,
                'galeria_id'   : galeria.id,
            }
            post_ser = PostagemSerializer(data=post_data, context={'request': request})
            post_ser.is_valid(raise_exception=True)
            post_ser.save()

        # 4) devolve sempre os dados da Galeria
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['PUT'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([AllowAny])
def galeria_update(request, id):
    galeria = get_object_or_404(Galeria, id=id)
    serializer = GaleriaSerializer(
        galeria, data=request.data, partial=True,
        context={'request': request}
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)

@api_view(['DELETE'])
def galeria_delete(request, id):
    try:
        galeria_ = Galeria.objects.get(id=id)
    except Galeria.DoesNotExist:
        return JsonResponse({"message": "Galeria not found."}, status=status.HTTP_208_ALREADY_REPORTED)
    
    if request.method == 'DELETE':
        galeria_.delete()
        return JsonResponse({"message": "Galeria deleted successfully"}, status=status.HTTP_200_OK)


@api_view(['GET'])
def galeria_list_by_utilizador(request, utilizador_id):
    # ─── validar utilizador ───────────────────────────────────────────
    try:
        Utilizador.objects.get(id=utilizador_id, status='ativo')
    except Utilizador.DoesNotExist:
        return Response({'detail': 'Utilizador não encontrado'}, status=404)

    #order by the most recent post
    qs = Galeria.objects.filter(utilizador_id=utilizador_id).order_by('-data')

    # ─── pesquisa opcional ────────────────────────────────────────────
    q = request.GET.get('q')
    if q:
        qs = qs.filter(titulo__icontains=q)

    # ─── paginação offset / limit ─────────────────────────────────────
    try:
        offset = int(request.GET.get('offset', 0))
        limit  = min(int(request.GET.get('limit', 5)), 50)
        if offset < 0 or limit <= 0:
            raise ValueError
    except ValueError:
        return Response({'detail': 'offset/limit inválidos'}, status=400)

    total   = qs.count()
    results = (qs
               .select_related('utilizador')   # ← nome do campo FK
               [offset : offset + limit])

    serializer = GaleriaSerializer(results, many=True,
                                   context={'request': request})

    return Response({
        'count'      : total,
        'next_offset': offset + limit if offset + limit < total else None,
        'results'    : serializer.data,
    }, status=status.HTTP_200_OK)


