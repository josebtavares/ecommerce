from django.urls import path
from ..Views import paginaView as v

urlpatterns = [
    # ── Público (rodapé da home) ──────────────────────────────
    path('paginas/',                   v.pagina_list_publica, name='pagina-list'),
    path('plataforma/publica/',        v.plataforma_publica,  name='plataforma-publica'),
    path('paginas/<slug:slug>/',       v.pagina_get_publica,  name='pagina-get'),

    # ── Admin ─────────────────────────────────────────────────
    path('admin/paginas/',             v.admin_pagina_list,   name='admin-pagina-list'),
    path('admin/paginas/<slug:slug>/', v.admin_pagina_editar, name='admin-pagina-editar'),
]
