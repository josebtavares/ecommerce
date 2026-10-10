"""
Que tipos de produto cada contexto pode usar:
  - produto da loja (backoffice ou POS integrado/híbrido): globais + os da loja
  - produto próprio do POS (standalone/híbrido):            globais + os do POS
"""
from django.db.models import Q

from ..models import TipoProduto


def tipos_para_loja(loja):
    return TipoProduto.objects.filter(
        Q(loja__isnull=True, pos__isnull=True) | Q(loja=loja), ativo=True
    )


def tipos_para_pos(pos):
    return TipoProduto.objects.filter(
        Q(loja__isnull=True, pos__isnull=True) | Q(pos=pos), ativo=True
    )


def tipo_permitido(qs, tipo_id):
    """Devolve o tipo se pertencer ao queryset permitido; None se tipo_id vazio; False se proibido."""
    if tipo_id in (None, '', 'null'):
        return None
    try:
        return qs.get(id=int(tipo_id))
    except (TipoProduto.DoesNotExist, ValueError, TypeError):
        return False
