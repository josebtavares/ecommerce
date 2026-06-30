from django.urls import path
from . import views

urlpatterns = [
    # ── AUTENTICAÇÃO ─────────────────────────────────────────────────
    path('login/',        views.pos_login,        name='pos_login'),
    path('login/membro/', views.pos_membro_login, name='pos_membro_login'),  # NOVO
    path('register/',     views.pos_register,     name='pos_register'),

    # ── CONFIGURAÇÃO POS ──────────────────────────────────────────────
    path('criar/',                           views.pos_criar,           name='pos_criar'),
    path('<int:pos_id>/',                    views.pos_detalhe,         name='pos_detalhe'),
    path('<int:pos_id>/conectar-loja/',      views.pos_conectar_loja,   name='pos_conectar_loja'),
    path('<int:pos_id>/desconectar-loja/',   views.pos_desconectar_loja,name='pos_desconectar_loja'),

    # ── PRODUTOS ──────────────────────────────────────────────────────
    path('<int:pos_id>/produtos/',                          views.pos_produtos,      name='pos_produtos'),
    path('<int:pos_id>/produtos/criar/',                    views.produto_criar,     name='produto_criar'),
    path('<int:pos_id>/produtos/<int:produto_id>/',         views.produto_atualizar, name='produto_atualizar'),
    path('<int:pos_id>/produtos/<int:produto_id>/apagar/',  views.produto_apagar,    name='produto_apagar'),

    # ── MESAS ─────────────────────────────────────────────────────────
    path('<int:pos_id>/mesas/',                        views.mesas_listar, name='mesas_listar'),
    path('<int:pos_id>/mesas/criar/',                  views.mesa_criar,   name='mesa_criar'),
    path('<int:pos_id>/mesas/<int:mesa_id>/abrir/',    views.mesa_abrir,   name='mesa_abrir'),
    path('<int:pos_id>/mesas/<int:mesa_id>/apagar/',   views.mesa_apagar,  name='mesa_apagar'),

    # ── CONTAS ────────────────────────────────────────────────────────
    path('<int:pos_id>/mesas/<int:mesa_id>/conta/',                          views.conta_criar,          name='conta_criar'),
    path('<int:pos_id>/contas/ativas/',                                      views.contas_ativas,        name='contas_ativas'),
    path('<int:pos_id>/historico/',                                          views.pos_historico,        name='pos_historico'),
    path('<int:pos_id>/contas/<int:conta_id>/',                              views.conta_detalhe,        name='conta_detalhe'),
    path('<int:pos_id>/contas/<int:conta_id>/items/',                        views.conta_adicionar_item, name='conta_adicionar_item'),
    path('<int:pos_id>/contas/<int:conta_id>/items/<int:item_id>/',          views.conta_remover_item,   name='conta_remover_item'),
    path('<int:pos_id>/contas/<int:conta_id>/items/<int:item_id>/status/',   views.item_status_atualizar,name='item_status_atualizar'),
    path('<int:pos_id>/contas/<int:conta_id>/fechar/',                       views.conta_fechar,         name='conta_fechar'),

    # ── TURNOS ────────────────────────────────────────────────────────
    path('<int:pos_id>/turnos/abrir/',                   views.turno_abrir,  name='turno_abrir'),
    path('<int:pos_id>/turnos/<int:turno_id>/fechar/',   views.turno_fechar, name='turno_fechar'),

    # ── EQUIPA ────────────────────────────────────────────────────────
    path('<int:pos_id>/equipa/',                        views.pos_equipa,        name='pos_equipa'),
    path('<int:pos_id>/equipa/<int:membro_id>/',        views.pos_equipa_membro, name='pos_equipa_membro'),
]