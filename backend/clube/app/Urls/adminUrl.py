from django.urls import path
from ..Views import adminView

urlpatterns = [

    # ── Estatísticas ──────────────────────────────────────────
    path('admin/stats/',                        adminView.admin_stats,               name='admin-stats'),

    # ── Lojas ─────────────────────────────────────────────────
    path('admin/lojas/',                        adminView.admin_loja_list,           name='admin-loja-list'),
    path('admin/lojas/<int:loja_id>/',          adminView.admin_loja_gerir,          name='admin-loja-gerir'),

    # ── Utilizadores ──────────────────────────────────────────
    path('admin/utilizadores/',                 adminView.admin_utilizador_list,     name='admin-utilizador-list'),
    path('admin/utilizadores/<int:utilizador_id>/', adminView.admin_utilizador_gerir, name='admin-utilizador-gerir'),

    # ── Produtos ──────────────────────────────────────────────
    path('admin/produtos/',                     adminView.admin_produto_list,        name='admin-produto-list'),
    path('admin/produtos/<int:produto_id>/',    adminView.admin_produto_gerir,       name='admin-produto-gerir'),

    # ── Encomendas ────────────────────────────────────────────
    path('admin/encomendas/',                   adminView.admin_encomenda_list,      name='admin-encomenda-list'),

    # ── Pagamentos ────────────────────────────────────────────
    path('admin/pagamentos/',                   adminView.admin_pagamento_list,      name='admin-pagamento-list'),

    # ── Tipos de produto globais ──────────────────────────────
    path('admin/tipos/',                        adminView.admin_tipos_list_criar,    name='admin-tipos-list'),
    path('admin/tipos/<int:tipo_id>/',          adminView.admin_tipos_gerir,         name='admin-tipos-gerir'),
    
     # ── Comissoes ──────────────────────────────────────────────
    path('admin/comissoes/',                        adminView.admin_comissao_list,          name='admin-comissao-list'),
    path('admin/comissoes/<int:comissao_id>/liquidar/', adminView.admin_comissao_liquidar,  name='admin-comissao-liquidar'),
    path('admin/lojas/<int:loja_id>/comissao/',     adminView.admin_loja_comissao,          name='admin-loja-comissao'),
    path('admin/lojas/<int:loja_id>/comissao/editar/', adminView.admin_loja_comissao_update, name='admin-loja-comissao-update'),
    
    # ── Categorias ──────────────────────────────────────────────

    path('admin/categorias/', adminView.admin_categoria_list_criar, name='admin-cat-list'),
    path('admin/categorias/<int:cat_id>/', adminView.admin_categoria_gerir, name='admin-cat-gerir'),
]

   