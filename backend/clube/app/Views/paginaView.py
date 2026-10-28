from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from ..models import ConfiguracaoPlataforma, PaginaInstitucional
from .adminView import _exige_admin


CAMPOS_CONTACTO = ('email', 'telefone', 'whatsapp', 'morada', 'horario')


def contactos_plataforma(cfg=None):
    """Contactos do site (Admin → Plataforma) — rodapé e página Contacto."""
    cfg = cfg or ConfiguracaoPlataforma.atual()
    return {k: getattr(cfg, f'contacto_{k}') for k in CAMPOS_CONTACTO}


def _serializar(p, completo=True):
    data = {
        'slug':   p.slug,
        'seccao': p.seccao,
        'titulo': p.titulo,
        'ativo':  p.ativo,
        'ordem':  p.ordem,
    }
    if completo:
        data.update({
            'conteudo':         p.conteudo,
            'dados':            p.dados or {},
            'data_atualizacao': p.data_atualizacao,
            'atualizado_por':   p.atualizado_por.nome if p.atualizado_por else None,
        })
    return data


def _limpar_dados(slug, dados):
    """Só guarda os campos estruturados que fazem sentido para cada página."""
    if not isinstance(dados, dict):
        return {}
    if slug == 'faq':
        perguntas = []
        for item in dados.get('perguntas') or []:
            if not isinstance(item, dict):
                continue
            pergunta = str(item.get('pergunta') or '').strip()[:300]
            resposta = str(item.get('resposta') or '').strip()[:4000]
            if pergunta:
                perguntas.append({'pergunta': pergunta, 'resposta': resposta})
        return {'perguntas': perguntas[:100]}
    return {}       # contacto: os contactos editam-se em Admin → Plataforma


# ══════════════════════════════════════════════════════════════
# PÚBLICO — rodapé da home
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([AllowAny])
def pagina_list_publica(request):
    """GET /app/paginas/ — páginas activas (sem conteúdo) para montar o rodapé."""
    paginas = PaginaInstitucional.objects.filter(ativo=True)
    return Response([_serializar(p, completo=False) for p in paginas])


@api_view(['GET'])
@permission_classes([AllowAny])
def pagina_get_publica(request, slug):
    """GET /app/paginas/<slug>/ — conteúdo de uma página activa."""
    p = get_object_or_404(PaginaInstitucional, slug=slug, ativo=True)
    data = _serializar(p)
    data.pop('atualizado_por', None)
    if p.slug == 'contacto':
        data['dados'] = contactos_plataforma()
    return Response(data)


@api_view(['GET'])
@permission_classes([AllowAny])
def plataforma_publica(request):
    """GET /app/plataforma/publica/ — o rodapé de todas as páginas: quem explora o site, contactos,
    páginas activas e se mostra os logótipos dos cartões."""
    cfg = ConfiguracaoPlataforma.atual()
    return Response({
        'titular_nome': cfg.titular_nome,
        'titular_nif': cfg.titular_nif,
        'contactos': contactos_plataforma(cfg),
        'mostrar_logos_pagamento': cfg.mostrar_logos_pagamento,
        'paginas': [_serializar(p, completo=False) for p in PaginaInstitucional.objects.filter(ativo=True)],
    })


# ══════════════════════════════════════════════════════════════
# ADMIN — edição
# ══════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_pagina_list(request):
    """GET /app/admin/paginas/"""
    erro = _exige_admin(request, 'gerir_conteudo')
    if erro: return erro
    return Response([_serializar(p) for p in PaginaInstitucional.objects.select_related('atualizado_por__user')])


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def admin_pagina_editar(request, slug):
    """
    PATCH /app/admin/paginas/<slug>/
    Body: { titulo?, conteudo?, dados?, ativo? }
    """
    erro = _exige_admin(request, 'gerir_conteudo')
    if erro: return erro

    p = get_object_or_404(PaginaInstitucional, slug=slug)

    if 'titulo' in request.data:
        titulo = str(request.data['titulo'] or '').strip()
        if not titulo:
            return Response({'detail': 'O título não pode ficar vazio.'}, status=status.HTTP_400_BAD_REQUEST)
        p.titulo = titulo[:120]
    if 'conteudo' in request.data:
        p.conteudo = str(request.data['conteudo'] or '')[:50000]
    if 'dados' in request.data:
        p.dados = _limpar_dados(p.slug, request.data['dados'])
    if 'ativo' in request.data:
        valor = request.data['ativo']
        p.ativo = valor if isinstance(valor, bool) else str(valor).lower() in ('true', '1')

    p.atualizado_por = request.user.utilizador
    p.save()
    return Response(_serializar(p))
