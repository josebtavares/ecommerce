from django.urls import path
from ..Views import categorialojaView

urlpatterns = [

    # ── Público ──────────────────────────────────────────────
    path('loja/<int:loja_id>/categorias/',
         categorialojaView.categoria_loja_list_publica,
         name='categoria-loja-publica'),

    path('categorias-destaque/',
         categorialojaView.categoria_destaque_list_publica,
         name='categoria-destaque-publica'),

    # ── Backoffice da loja ───────────────────────────────────
    path('loja/<int:loja_id>/categorias/gerir/',
         categorialojaView.categoria_loja_list_backoffice,
         name='categoria-loja-list'),

    path('loja/<int:loja_id>/categorias/criar/',
         categorialojaView.categoria_loja_criar,
         name='categoria-loja-criar'),

    path('loja/<int:loja_id>/categorias/<int:cat_id>/',
         categorialojaView.categoria_loja_gerir,
         name='categoria-loja-gerir'),

    path('loja/<int:loja_id>/categorias/<int:cat_id>/toggle/',
         categorialojaView.categoria_loja_toggle,
         name='categoria-loja-toggle'),

    path('loja/<int:loja_id>/categorias/<int:cat_id>/produtos/',
         categorialojaView.categoria_loja_adicionar_produto,
         name='categoria-loja-add-produto'),

    path('loja/<int:loja_id>/categorias/<int:cat_id>/produtos/<int:produto_id>/',
         categorialojaView.categoria_loja_remover_produto,
         name='categoria-loja-remove-produto'),

    # ── Admin ─────────────────────────────────────────────────
    path('admin/categorias-destaque/',
         categorialojaView.categoria_destaque_list_admin,
         name='categoria-destaque-admin-list'),

    path('admin/categorias-destaque/lojas/',
         categorialojaView.categoria_destaque_lojas_admin,
         name='categoria-destaque-lojas'),

    path('admin/categorias-destaque/disponiveis/',
         categorialojaView.categoria_destaque_disponiveis,
         name='categoria-destaque-disponiveis'),

    path('admin/categorias-destaque/criar/',
         categorialojaView.categoria_destaque_criar,
         name='categoria-destaque-criar'),

    path('admin/categorias-destaque/<int:destaque_id>/',
         categorialojaView.categoria_destaque_gerir,
         name='categoria-destaque-gerir'),

    path('admin/categorias-destaque/<int:destaque_id>/toggle/',
         categorialojaView.categoria_destaque_toggle,
         name='categoria-destaque-toggle'),
]

# Remover do produtoUrl.py:
# path('loja/<int:loja_id>/produtos/categorias/', ...)
# Adicionar ao urls.py principal:
# from .Views.categoriaLojaUrl import urlpatterns as categoria_urls
# urlpatterns += categoria_urls