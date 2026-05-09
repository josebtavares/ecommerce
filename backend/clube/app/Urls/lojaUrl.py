from django.urls import path
from ..Views import lojaView

urlpatterns = [

 

    # ── Leitura pública ───────────────────────────────────────
    path('loja/',                                       lojaView.loja_list,             name='loja-list'),
    path('loja/<int:id>/',                              lojaView.loja_get,              name='loja-get'),

    # ── Criar loja (utilizador autenticado) ───────────────────
    path('loja/criar/',                                 lojaView.loja_create,           name='loja-criar'),

    # ── Lojas do utilizador autenticado ───────────────────────
    path('loja/minhas/',                                lojaView.minhas_lojas,          name='loja-minhas'),

    # ── Backoffice ────────────────────────────────────────────
    path('loja/<int:id>/backoffice/',                   lojaView.loja_backoffice,       name='loja-backoffice'),
    path('loja/<int:id>/editar/',                       lojaView.loja_update,           name='loja-update'),
    path('loja/<int:id>/eliminar/',                     lojaView.loja_delete,           name='loja-delete'),
    path('loja/<int:loja_id>/dashboard/',               lojaView.loja_dashboard,        name='loja-dashboard'),

    # ── Staff ─────────────────────────────────────────────────
    path('loja/<int:loja_id>/staff/',                   lojaView.staff_list,            name='staff-list'),
    path('loja/<int:loja_id>/staff/adicionar/',         lojaView.staff_add,             name='staff-add'),
    path('loja/<int:loja_id>/staff/<int:membro_id>/',   lojaView.staff_update_role,     name='staff-update'),
    path('loja/<int:loja_id>/staff/<int:membro_id>/remover/', lojaView.staff_remove,    name='staff-remove'),
    
    # ── Categorias ─────────────────────────────────────────────────
    path('categorias/', lojaView.categoria_list, name='categoria-list'),
    
    path('loja/<int:loja_id>/pagamento/metodos/', lojaView.metodos_pagamento_publico),
    
    
    # ── Aparencias ─────────────────────────────────────────────────
    path('loja/<int:loja_id>/aparencia/', lojaView.loja_aparencia, name='loja-aparencia'),
    
    # ── Criar Utilizador da loja ─────────────────────────────────────────────────

    path('loja/<int:loja_id>/staff/criar-utilizador/', lojaView.staff_criar_utilizador),
]