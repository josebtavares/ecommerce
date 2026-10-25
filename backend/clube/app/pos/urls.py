from django.urls import path
from . import views, views_variantes, views_conjuntos, views_subscricao, views_relatorios, views_faturacao

urlpatterns = [
    # ── AUTENTICAÇÃO ─────────────────────────────────────────────────
    path('login/',        views.pos_login,        name='pos_login'),
    path('login/membro/', views.pos_membro_login, name='pos_membro_login'),  # NOVO
    path('login/google/', views.pos_login_google, name='pos_login_google'),
    path('register/',     views.pos_register,     name='pos_register'),

    # ── CONFIGURAÇÃO POS ──────────────────────────────────────────────
    path('meus/',                            views.pos_meus,            name='pos_meus'),
    path('planos/',                          views_subscricao.planos_pos, name='pos_planos'),
    path('<int:pos_id>/subscricao/',         views_subscricao.pos_subscricao, name='pos_subscricao'),
    path('<int:pos_id>/subscricao/plano/',   views_subscricao.pos_subscricao_plano, name='pos_subscricao_plano'),
    path('<int:pos_id>/subscricao/loja/',    views_subscricao.pos_subscricao_loja, name='pos_subscricao_loja'),
    path('<int:pos_id>/subscricao/faturas/',  views_subscricao.pos_subscricao_faturas, name='pos_subscricao_faturas'),
    path('<int:pos_id>/subscricao/faturas/<int:fatura_id>/pagar/', views_subscricao.pos_fatura_pagar, name='pos_fatura_pagar'),
    path('criar/',                           views.pos_criar,           name='pos_criar'),
    path('<int:pos_id>/',                    views.pos_detalhe,         name='pos_detalhe'),
    path('<int:pos_id>/fiscal/',             views.pos_dados_fiscais,   name='pos_dados_fiscais'),
    path('<int:pos_id>/conectar-loja/',      views.pos_conectar_loja,   name='pos_conectar_loja'),
    path('<int:pos_id>/desconectar-loja/',   views.pos_desconectar_loja,name='pos_desconectar_loja'),

    # ── PRODUTOS ──────────────────────────────────────────────────────
    path('<int:pos_id>/produtos/',                          views.pos_produtos,      name='pos_produtos'),
    path('<int:pos_id>/produtos/criar/',                    views.produto_criar,     name='produto_criar'),
    path('<int:pos_id>/produtos/<int:produto_id>/',         views.produto_atualizar, name='produto_atualizar'),
    path('<int:pos_id>/produtos/<int:produto_id>/apagar/',  views.produto_apagar,    name='produto_apagar'),
    path('<int:pos_id>/produtos/<int:produto_id>/variantes/', views_variantes.pos_produto_variantes, name='pos_produto_variantes'),
    path('<int:pos_id>/produtos/<int:produto_id>/componentes/<int:componente_id>/substituir/',
         views_conjuntos.conjunto_substituir_componente, name='pos_conjunto_substituir'),

    # ── TIPOS DE PRODUTO ──────────────────────────────────────────────
    path('<int:pos_id>/tipos/',                    views_variantes.pos_tipos,      name='pos_tipos'),
    path('<int:pos_id>/tipos/<int:tipo_id>/',      views_variantes.pos_tipo_gerir, name='pos_tipo_gerir'),

    # ── MESAS ─────────────────────────────────────────────────────────
    path('<int:pos_id>/mesas/',                        views.mesas_listar, name='mesas_listar'),
    path('<int:pos_id>/mesas/criar/',                  views.mesa_criar,   name='mesa_criar'),
    path('<int:pos_id>/mesas/<int:mesa_id>/abrir/',    views.mesa_abrir,   name='mesa_abrir'),
    path('<int:pos_id>/mesas/<int:mesa_id>/apagar/',   views.mesa_apagar,  name='mesa_apagar'),

    # ── CONTAS ────────────────────────────────────────────────────────
    path('<int:pos_id>/mesas/<int:mesa_id>/conta/',                          views.conta_criar,          name='conta_criar'),
    path('<int:pos_id>/contas/ativas/',                                      views.contas_ativas,        name='contas_ativas'),
    path('<int:pos_id>/painel/',                       views_relatorios.pos_painel,        name='pos_painel'),
    path('<int:pos_id>/relatorios/catalogo/',          views_relatorios.pos_rel_catalogo,  name='pos_rel_catalogo'),
    path('<int:pos_id>/relatorios/historico/',         views_relatorios.pos_rel_historico, name='pos_rel_historico'),
    path('<int:pos_id>/relatorios/r/<slug:rid>/',      views_relatorios.pos_rel_relatorio, name='pos_rel_relatorio'),
    path('<int:pos_id>/relatorios/r/<slug:rid>/exportar/', views_relatorios.pos_rel_exportar, name='pos_rel_exportar'),
    path('<int:pos_id>/historico/',                                          views.pos_historico,        name='pos_historico'),
    path('<int:pos_id>/contas/<int:conta_id>/',                              views.conta_detalhe,        name='conta_detalhe'),
    path('<int:pos_id>/contas/<int:conta_id>/items/',                        views.conta_adicionar_item, name='conta_adicionar_item'),
    path('<int:pos_id>/contas/<int:conta_id>/items/<int:item_id>/',          views.conta_remover_item,   name='conta_remover_item'),
    path('<int:pos_id>/contas/<int:conta_id>/items/<int:item_id>/status/',   views.item_status_atualizar,name='item_status_atualizar'),
    path('<int:pos_id>/contas/<int:conta_id>/fechar/',                       views.conta_fechar,         name='conta_fechar'),
    path('<int:pos_id>/contas/<int:conta_id>/cancelar/',                     views.conta_cancelar,       name='conta_cancelar'),
    path('<int:pos_id>/contas/<int:conta_id>/fatura/',                       views.conta_fatura,         name='conta_fatura'),
    # faturação (views_faturacao.py)
    path('<int:pos_id>/faturacao/resumo/',     views_faturacao.resumo,     name='pos_faturacao_resumo'),
    path('<int:pos_id>/faturacao/vendas/',     views_faturacao.vendas,     name='pos_faturacao_vendas'),
    path('<int:pos_id>/faturacao/vendas.csv',  views_faturacao.vendas_csv, name='pos_faturacao_vendas_csv'),
    path('<int:pos_id>/faturacao/exportar/',   views_faturacao.exportar,   name='pos_faturacao_exportar'),
    path('<int:pos_id>/faturacao/pesquisa/',   views_faturacao.pesquisa,   name='pos_faturacao_pesquisa'),
    path('<int:pos_id>/faturacao/historico/',  views_faturacao.historico,  name='pos_faturacao_historico'),

    # ── TURNOS ────────────────────────────────────────────────────────
    path('<int:pos_id>/turnos/atual/',                   views.turno_atual,  name='turno_atual'),
    path('<int:pos_id>/turnos/abrir/',                   views.turno_abrir,  name='turno_abrir'),
    path('<int:pos_id>/turnos/<int:turno_id>/fechar/',   views.turno_fechar, name='turno_fechar'),

    # ── EQUIPA ────────────────────────────────────────────────────────
    path('<int:pos_id>/equipa/',                        views.pos_equipa,        name='pos_equipa'),
    path('<int:pos_id>/equipa/<int:membro_id>/',        views.pos_equipa_membro, name='pos_equipa_membro'),
    
    # ── USERNAME CHECK ────────────────────────────────────────────────────────

    path('<int:pos_id>/equipa/verificar-username/', views.pos_verificar_username, name='pos_verificar_username'),

]