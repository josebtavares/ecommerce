from django.urls import path
from ..Views import aparenciaView as ap
from ..Views import paginaView as v

urlpatterns = [
    # ── Público (rodapé da home) ──────────────────────────────
    path('paginas/',                   v.pagina_list_publica, name='pagina-list'),
    path('plataforma/publica/',        v.plataforma_publica,  name='plataforma-publica'),
    path('plataforma/aparencia/',      ap.aparencia_publica,  name='aparencia-publica'),

    # ── Aparência (Admin → Definições) ────────────────────────
    path('admin/plataforma/aparencia/',       ap.admin_aparencia,       name='admin-aparencia'),
    path('admin/plataforma/aparencia/fundo/', ap.admin_aparencia_fundo, name='admin-aparencia-fundo'),
    path('admin/plataforma/aparencia/logo/',  ap.admin_aparencia_logo,  name='admin-aparencia-logo'),
    path('paginas/<slug:slug>/',       v.pagina_get_publica,  name='pagina-get'),

    # ── Admin ─────────────────────────────────────────────────
    path('admin/paginas/',             v.admin_pagina_list,   name='admin-pagina-list'),
    path('admin/paginas/<slug:slug>/', v.admin_pagina_editar, name='admin-pagina-editar'),
]
