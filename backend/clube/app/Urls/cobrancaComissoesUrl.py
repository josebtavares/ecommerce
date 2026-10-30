from django.urls import path
from ..Views import cobrancaComissoesView as v

urlpatterns = [
    path('loja/<int:loja_id>/comissoes/cobrancas/',                        v.loja_cobrancas,         name='loja-cobrancas'),
    path('loja/<int:loja_id>/comissoes/cobrancas/<int:cobranca_id>/pagar/', v.loja_cobranca_pagar,    name='loja-cobranca-pagar'),
    path('admin/comissoes/cobrancas/',                                     v.admin_cobrancas,        name='admin-cobrancas'),
    path('admin/comissoes/cobrancas/emitir/',                              v.admin_cobrancas_emitir, name='admin-cobrancas-emitir'),
    path('admin/comissoes/cobrancas/<int:cobranca_id>/',                   v.admin_cobranca,         name='admin-cobranca'),
]
