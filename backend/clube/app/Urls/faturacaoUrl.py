from django.urls import path
from ..Views import faturacaoView as v

# documentos internos e faturas registadas (ver app/Views/faturacaoView.py)
urlpatterns = [
    path('encomenda/<int:id>/comprovativo/',                     v.encomenda_comprovativo,  name='encomenda-comprovativo'),
    path('subscricao/faturas/<int:fatura_id>/comprovativo/',    v.subscricao_comprovativo, name='subscricao-comprovativo'),
    path('loja/<int:loja_id>/comissoes/meses/',                 v.loja_comissoes_meses,    name='loja-comissoes-meses'),
    path('loja/<int:loja_id>/comissoes/<str:mes>/vendas/',      v.loja_comissoes_vendas,   name='loja-comissoes-vendas'),
    path('loja/<int:loja_id>/comissoes/<str:mes>/extrato/',     v.loja_comissoes_extrato,  name='loja-comissoes-extrato'),
    path('admin/faturacao/vendedores/',                         v.admin_vendedores,        name='admin-faturacao-vendedores'),
    path('admin/faturacao/ficha/<str:tipo>/<int:id>/',           v.admin_ficha,             name='admin-faturacao-ficha'),
    path('admin/faturacao/loja/<int:loja_id>/vendas/',          v.admin_loja_vendas,       name='admin-faturacao-loja-vendas'),
    path('admin/faturacao/pos/<int:pos_id>/vendas/',            v.admin_pos_vendas,        name='admin-faturacao-pos-vendas'),
    path('admin/faturacao/historico/',                          v.admin_historico,         name='admin-faturacao-historico'),
    path('admin/faturacao/pesquisa/',                           v.admin_pesquisa,          name='admin-faturacao-pesquisa'),
    path('admin/faturacao/exportar/<str:tipo>/<int:id>/',       v.admin_exportar,          name='admin-faturacao-exportar'),
    path('admin/faturacao/abas/',                               v.admin_abas,              name='admin-faturacao-abas'),
    path('admin/faturacao/vendas.csv',                          v.admin_vendas_csv,        name='admin-faturacao-vendas'),
    path('admin/faturacao/bende/',                              v.admin_bende,             name='admin-faturacao-bende'),
    path('admin/faturacao/subscricoes/<int:fatura_id>/fatura/', v.admin_fatura_subscricao, name='admin-faturacao-subscricao'),
    path('admin/faturacao/comissoes/<int:loja_id>/<str:mes>/fatura/',  v.admin_fatura_comissoes,  name='admin-faturacao-comissoes'),
    path('admin/faturacao/comissoes/<int:loja_id>/<str:mes>/extrato/', v.admin_comissoes_extrato, name='admin-faturacao-extrato'),
]
