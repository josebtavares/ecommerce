from django.urls import path
from ..Views import lojaCartaoView as c
from ..Views import vinti4View as v

urlpatterns = [
    path('loja/<int:loja_id>/vinti4/',        v.loja_vinti4,        name='loja-vinti4'),
    path('admin/lojas/<int:loja_id>/vinti4/', v.admin_loja_vinti4,  name='admin-loja-vinti4'),
    # backoffice → Pagamentos (pagamentos com cartão da loja)
    path('loja/<int:loja_id>/cartao/',                              c.lista,        name='loja-cartao'),
    path('loja/<int:loja_id>/cartao/csv/',                          c.csv,          name='loja-cartao-csv'),
    path('loja/<int:loja_id>/cartao/vbvt/',                         c.vbvt,         name='loja-cartao-vbvt'),
    path('loja/<int:loja_id>/cartao/vbvt/<int:ficheiro_id>/',       c.vbvt_detalhe, name='loja-cartao-vbvt-detalhe'),
    path('loja/<int:loja_id>/cartao/<int:tx_id>/',                  c.detalhe,      name='loja-cartao-detalhe'),
    path('loja/<int:loja_id>/cartao/<int:tx_id>/consultar/',        c.consultar,    name='loja-cartao-consultar'),
]
