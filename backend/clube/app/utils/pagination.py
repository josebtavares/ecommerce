# app/utils/pagination.py
# ══════════════════════════════════════════════════════════════
# Helper de paginação reutilizável em todas as views
# ══════════════════════════════════════════════════════════════
# Uso:
#   from ..utils.pagination import paginar
#   return paginar(request, qs, MeuSerializer)

from rest_framework.response import Response
from rest_framework import status


DEFAULT_LIMIT = 20
MAX_LIMIT     = 100


def paginar(request, qs, serializer_cls, limit_default=DEFAULT_LIMIT):
    """
    Aplica paginação offset/limit a qualquer queryset.

    Query params:
      offset  – índice de início  (default: 0)
      limit   – número de itens   (default: 20, max: 100)

    Resposta:
      {
        "count":       <total de resultados>,
        "next_offset": <próximo offset ou null se não há mais>,
        "results":     [...]
      }
    """
    try:
        offset = max(int(request.GET.get('offset', 0)), 0)
        limit  = min(int(request.GET.get('limit', limit_default)), MAX_LIMIT)
        if limit <= 0:
            raise ValueError
    except ValueError:
        return None, Response(
            {'detail': 'offset/limit inválidos.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    total   = qs.count()
    results = qs[offset: offset + limit]
    has_more = offset + limit < total

    serializer = serializer_cls(
        results, many=True,
        context={'request': request}
    )

    return Response({
        'count'      : total,
        'next_offset': offset + limit if has_more else None,
        'results'    : serializer.data,
    }), None