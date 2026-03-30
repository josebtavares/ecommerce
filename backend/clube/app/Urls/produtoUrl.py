from django.urls import path
from ..Views import produtoView

urlpatterns = [

    # ── Tipos de produto (público) ────────────────────────────
    path('produto/tipos/',                          produtoView.tipo_produto_list,       name='tipo-produto-list'),

    # ── Leitura pública ───────────────────────────────────────
    path('produto/',                                produtoView.produto_list_pagination,  name='produto-list'),
    path('produto/<int:id>/',                       produtoView.produto_get,              name='produto-get'),
    
    # Tipos por loja
    path('loja/<int:loja_id>/tipos/',               produtoView.tipo_produto_list_loja, name='tipo-list-loja'),
    path('loja/<int:loja_id>/tipos/criar/',          produtoView.tipo_produto_criar,     name='tipo-criar'),
    path('loja/<int:loja_id>/tipos/<int:tipo_id>/',  produtoView.tipo_produto_gerir,     name='tipo-gerir'),

    # ── Backoffice da loja (requer autenticação + permissão) ──
    path('loja/<int:loja_id>/produtos/',            produtoView.produto_list_loja,        name='produto-list-loja'),
    path('loja/<int:loja_id>/produtos/criar/',      produtoView.produto_create,           name='produto-create'),
    path('loja/<int:loja_id>/produtos/<int:id>/editar/',  produtoView.produto_update,     name='produto-update'),
    path('loja/<int:loja_id>/produtos/<int:id>/eliminar/', produtoView.produto_delete,    name='produto-delete'),
]