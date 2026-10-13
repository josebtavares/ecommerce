"""
Menus (conjuntos) do POS — substituir um componente.

Num POS híbrido um menu pode levar produtos da loja Bendi. Se a loja for suspensa (ou
desligada do POS), o menu fica indisponível; o dono corrige-o trocando esse componente por:
  - um produto do POS que já exista   → {"produto_pos_id": 12, "variante_pos_id": 3?}
  - uma cópia criada agora no POS     → {"criar": true, "controlar_stock": true, "stock": 0}
    (mesmo nome, preço, descrição e foto; o stock da loja não passa para o POS)
"""
import os

from django.core.files.base import ContentFile
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response

from .permissions import POSAuthentication, IsPOSAuthenticated
from .models import ProdutoPOS, VarianteProdutoPOS, ComponenteConjuntoPOS
from .views import _resolve_pos_request, _produto_pos_payload, _str_to_bool

VIDEO = ('.mp4', '.webm', '.mov', '.mkv', '.m4v')


def _copiar_imagem(origem_ficheiro, destino):
    """Copia a foto do produto da loja para o produto do POS (ficheiro próprio — se a loja
    trocar ou apagar a dela, a do POS não se perde). Falha da storage → fica sem foto."""
    if not origem_ficheiro or str(origem_ficheiro.name).lower().endswith(VIDEO):
        return
    try:
        with origem_ficheiro.open('rb') as f:
            dados = f.read()
        destino.imagem.save(os.path.basename(origem_ficheiro.name), ContentFile(dados), save=False)
    except Exception:
        pass


def _copia_no_pos(pos, comp, controlar_stock, stock):
    """Cria no POS um produto igual ao componente da loja (na variação que o menu usava)."""
    p, v = comp.produto, comp.variante
    tipo = p.tipo if (p.tipo_id and v is None and p.tipo.loja_id is None and p.tipo.pos_id is None) else None
    cat = p.categorias.first()
    novo = ProdutoPOS(
        pos=pos,
        nome=(p.nome + (f' ({v.descricao()})' if v else ''))[:200],
        descricao=p.descricao or '',
        categoria=(cat.nome if cat else 'Sem categoria')[:100],
        preco=v.preco_efetivo if v else p.preco,
        controlar_stock=controlar_stock,
        stock=max(stock, 0) if controlar_stock else 0,
        tipo=tipo,
        atributos=(p.atributos or {}) if tipo else {},
    )
    _copiar_imagem(p.ficheiro_poster if (p.ficheiro and str(p.ficheiro.name).lower().endswith(VIDEO)) else p.ficheiro, novo)
    novo.save()
    return novo


@api_view(['POST'])
@authentication_classes([POSAuthentication])
@permission_classes([IsPOSAuthenticated])
@transaction.atomic
def conjunto_substituir_componente(request, pos_id, produto_id, componente_id):
    """POST /api/pos/<pos_id>/produtos/<produto_id>/componentes/<componente_id>/substituir/"""
    pos, membro, _ = _resolve_pos_request(request, pos_id, ativo=True)
    if membro and not membro.pode_gerir_produtos:
        return Response({'detail': 'Sem permissão para gerir produtos.'}, status=status.HTTP_403_FORBIDDEN)

    conjunto = get_object_or_404(ProdutoPOS, id=produto_id, pos=pos, e_conjunto=True)
    comp = get_object_or_404(ComponenteConjuntoPOS.objects.select_for_update(), id=componente_id, conjunto=conjunto)

    if _str_to_bool(request.data.get('criar'), False):
        if comp.produto_id is None:
            return Response({'detail': 'Este produto já é do POS — escolhe outro para o substituir.'},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            stock = int(request.data.get('stock') or 0)
        except (TypeError, ValueError):
            return Response({'detail': 'Stock inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        novo, variante_pos = _copia_no_pos(pos, comp, _str_to_bool(request.data.get('controlar_stock'), True), stock), None
    else:
        novo = get_object_or_404(ProdutoPOS, id=request.data.get('produto_pos_id'), pos=pos)
        if novo.pk == conjunto.pk or novo.e_conjunto:
            return Response({'detail': 'Não se pode pôr um menu dentro de outro.'}, status=status.HTTP_400_BAD_REQUEST)
        if not novo.ativo:
            return Response({'detail': f'"{novo.nome}" está desactivado.'}, status=status.HTTP_400_BAD_REQUEST)
        variante_pos = None
        if novo.stock_por_variante:
            variante_pos = VarianteProdutoPOS.objects.filter(
                id=request.data.get('variante_pos_id'), produto=novo, ativo=True).first()
            if not variante_pos:
                return Response({'detail': f'Escolhe a variação de "{novo.nome}".'}, status=status.HTTP_400_BAD_REQUEST)
        repetido = (ComponenteConjuntoPOS.objects.filter(conjunto=conjunto, produto_pos=novo, variante_pos=variante_pos)
                    .exclude(id=comp.id).exists())
        if repetido:
            return Response({'detail': f'"{novo.nome}" já está neste menu — aumenta a quantidade em vez de o repetir.'},
                            status=status.HTTP_400_BAD_REQUEST)

    comp.produto, comp.variante = None, None
    comp.produto_pos, comp.variante_pos = novo, variante_pos
    comp.save()

    conjunto.refresh_from_db()
    return Response({
        'detail': f'Substituído por "{novo.nome}".',
        'produto_pos': _produto_pos_payload(novo, request, pos),
        'conjunto': _produto_pos_payload(conjunto, request, pos),
    })
