from django.urls import path
from ..Views import lojaView, videoView, horarioView, calendarioView

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
    path('loja/<int:id>/eliminar/',                     lojaView.loja_fechar,           name='loja-delete'),   # compat.: fecha, não apaga
    path('loja/<int:id>/fechar/',                       lojaView.loja_fechar,           name='loja-fechar'),
    path('loja/<int:id>/reabrir/',                      lojaView.loja_reabrir,          name='loja-reabrir'),
    path('loja/<int:loja_id>/dashboard/',               lojaView.loja_dashboard,        name='loja-dashboard'),
    path('loja/<int:loja_id>/videos/',                  videoView.videos_estado,        name='loja-videos'),
    path('loja/<int:loja_id>/videos/reprocessar/',      videoView.videos_reprocessar,   name='loja-videos-reprocessar'),

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
    path("loja/<int:loja_id>/horario/", horarioView.loja_horario, name="loja-horario"),
    path("admin/plataforma/", horarioView.admin_plataforma, name="admin-plataforma"),
    path("loja/<int:loja_id>/agendamento/vagas/", horarioView.loja_vagas, name="loja-vagas"),
    path("loja/<int:loja_id>/pausa/", horarioView.loja_pausa, name="loja-pausa"),
    path("loja/<int:loja_id>/estado/", horarioView.loja_estado, name="loja-estado"),
    path("loja/<int:loja_id>/entrega/calendario/", calendarioView.entrega_calendario, name="entrega-calendario"),
    
    # ── Criar Utilizador da loja ─────────────────────────────────────────────────

    path('loja/<int:loja_id>/staff/criar-utilizador/', lojaView.staff_criar_utilizador),
]