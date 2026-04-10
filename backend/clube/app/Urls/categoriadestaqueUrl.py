from django.urls import path
from ..Views import categoriadestaqueView

urlpatterns = [
    # Público — home
    path('categorias-destaque/',
         categoriadestaqueView.categoria_destaque_list_publica,
         name='categoria-destaque-list'),

    # Admin — gestão
    path('admin/categorias-destaque/',
         categoriadestaqueView.categoria_destaque_list_admin,
         name='categoria-destaque-admin-list'),
    path('admin/categorias-destaque/criar/',
         categoriadestaqueView.categoria_destaque_criar,
         name='categoria-destaque-criar'),
    path('admin/categorias-destaque/<int:cat_id>/',
         categoriadestaqueView.categoria_destaque_gerir,
         name='categoria-destaque-gerir'),
    path('admin/categorias-destaque/<int:cat_id>/toggle/',
         categoriadestaqueView.categoria_destaque_toggle,
         name='categoria-destaque-toggle'),

    # Sugestões para backoffice da loja
    path('produto/categorias/sugestoes/',
         categoriadestaqueView.categoria_sugestoes,
         name='categoria-sugestoes'),
]

# Adicionar ao urls.py principal:
# from .Views.categoriaDestaqueUrl import urlpatterns as categoria_urls
# urlpatterns += categoria_urls