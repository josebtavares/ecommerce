from django.urls import path
from ..Views import exportacaoLojaView as v

# exportar os dados de uma loja ou de um POS (ver app/Views/exportacaoLojaView.py)
urlpatterns = [
    path('loja/<int:loja_id>/exportacoes/',                                     v.loja_exportacoes,                  name='loja-exportacoes'),
    path('loja/<int:loja_id>/exportacoes/<int:exportacao_id>/descarregar/',     v.loja_exportacao_descarregar,       name='loja-exportacao-descarregar'),
    path('admin/lojas/<int:loja_id>/exportacoes/',                              v.admin_loja_exportacoes,            name='admin-loja-exportacoes'),
    path('admin/lojas/<int:loja_id>/exportacoes/<int:exportacao_id>/descarregar/', v.admin_loja_exportacao_descarregar, name='admin-loja-exportacao-descarregar'),
    path('admin/pos/<int:pos_id>/exportacoes/',                                 v.admin_pos_exportacoes,             name='admin-pos-exportacoes'),
    path('admin/pos/<int:pos_id>/exportacoes/<int:exportacao_id>/descarregar/', v.admin_pos_exportacao_descarregar,  name='admin-pos-exportacao-descarregar'),
    path('exportacoes/ficheiro/<str:token>/',                                   v.exportacao_ficheiro,               name='exportacao-ficheiro'),
]
