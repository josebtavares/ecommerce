from django.urls import path
from ..Views import adminView
from ..Views import relatorioView
from ..Views import backupView
from ..pos import views_admin as pos_admin

urlpatterns = [

    # ── Estatísticas ──────────────────────────────────────────
    path('admin/stats/',                        adminView.admin_stats,               name='admin-stats'),
    path('admin/dashboard/',                    adminView.admin_dashboard,           name='admin-dashboard'),
    # ── Relatórios (catálogo, consulta e exportação) ───────────
    path('admin/relatorios/catalogo/',            relatorioView.admin_catalogo,  name='admin-relatorios-catalogo'),
    path('admin/relatorios/historico/',           relatorioView.admin_historico, name='admin-relatorios-historico'),
    path('admin/relatorios/r/<slug:rid>/',        relatorioView.admin_relatorio, name='admin-relatorio'),
    path('admin/relatorios/r/<slug:rid>/exportar/', relatorioView.admin_exportar, name='admin-relatorio-exportar'),
    # ── Backups da base de dados (só super-admin) ─────────────
    path('admin/backups/',                              backupView.admin_backups,            name='admin-backups'),
    path('admin/backups/descargas/',                    backupView.admin_backup_descargas,   name='admin-backup-descargas'),
    path('admin/backups/ensaiar/',                      backupView.admin_backup_ensaiar,     name='admin-backup-ensaiar'),
    path('admin/backups/media/copiar/',                 backupView.admin_backup_media_copiar, name='admin-backup-media-copiar'),
    path('admin/backups/fazer/',                        backupView.admin_backup_fazer,       name='admin-backup-fazer'),
    path('admin/backups/<int:backup_id>/descarregar/',  backupView.admin_backup_descarregar, name='admin-backup-descarregar'),
    path('admin/backups/ficheiro/<str:token>/',         backupView.admin_backup_ficheiro,    name='admin-backup-ficheiro'),
    # ── Lojas ─────────────────────────────────────────────────
    path('admin/lojas/',                        adminView.admin_loja_list,           name='admin-loja-list'),
    path('admin/lojas/<int:loja_id>/',          adminView.admin_loja_gerir,          name='admin-loja-gerir'),
    path('admin/lojas/<int:loja_id>/eliminar/', adminView.admin_loja_eliminar,       name='admin-loja-eliminar'),

    # ── Utilizadores ──────────────────────────────────────────
    path('admin/utilizadores/',                 adminView.admin_utilizador_list,     name='admin-utilizador-list'),
    path('admin/utilizadores/<int:utilizador_id>/', adminView.admin_utilizador_gerir, name='admin-utilizador-gerir'),
    path('admin/utilizadores/<int:utilizador_id>/moderar/', adminView.admin_utilizador_moderar, name='admin-utilizador-moderar'),

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
    path('admin/comissoes/por-loja/',               adminView.admin_comissoes_por_loja, name='admin-comissoes-por-loja'),
    path('admin/comissoes/creditos/',               adminView.admin_creditos_comissao,  name='admin-creditos-comissao'),
    path('admin/comissoes/creditos/descontar/',     adminView.admin_creditos_descontar, name='admin-creditos-descontar'),
    path('admin/comissoes/<int:comissao_id>/liquidar/', adminView.admin_comissao_liquidar,  name='admin-comissao-liquidar'),
    path('admin/lojas/<int:loja_id>/comissao/',     adminView.admin_loja_comissao,          name='admin-loja-comissao'),
    path('admin/lojas/<int:loja_id>/comissao/editar/', adminView.admin_loja_comissao_update, name='admin-loja-comissao-update'),
    
    # ── Categorias ──────────────────────────────────────────────

    path('admin/categorias/', adminView.admin_categoria_list_criar, name='admin-cat-list'),
    path('admin/categorias/<int:cat_id>/', adminView.admin_categoria_gerir, name='admin-cat-gerir'),
    
    #-─ Relatórios ──────────────────────────────────────────────
    path('admin/relatorios/', adminView.admin_relatorios, name='admin-relatorios'),

    #-─ POS (visão e suporte da plataforma) ───────────────────────
    path('admin/pos/',                                    pos_admin.admin_pos_list,           name='admin-pos-list'),
    path('admin/pos/<int:pos_id>/',                       pos_admin.admin_pos_detalhe,        name='admin-pos-detalhe'),
    path('admin/pos/<int:pos_id>/suspender/',             pos_admin.admin_pos_suspender,      name='admin-pos-suspender'),
    path('admin/pos/<int:pos_id>/reativar/',              pos_admin.admin_pos_reativar,       name='admin-pos-reativar'),
    path('admin/pos/<int:pos_id>/desligar-loja/',         pos_admin.admin_pos_desligar_loja,  name='admin-pos-desligar-loja'),
    path('admin/pos/<int:pos_id>/contas/<int:conta_id>/cancelar/', pos_admin.admin_pos_cancelar_conta, name='admin-pos-cancelar-conta'),
    path('admin/pos/<int:pos_id>/membros/<int:membro_id>/password/', pos_admin.admin_pos_membro_password, name='admin-pos-membro-password'),
]

   