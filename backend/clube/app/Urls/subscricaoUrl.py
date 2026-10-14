from django.urls import path
from ..Views import subscricaoView as v

urlpatterns = [
    path('planos/',                                                     v.planos_publicos,     name='planos-publicos'),
    # backoffice
    path('loja/<int:loja_id>/subscricao/',                              v.loja_subscricao,     name='loja-subscricao'),
    path('loja/<int:loja_id>/subscricao/faturas/<int:fatura_id>/pagar/', v.loja_fatura_pagar,  name='loja-fatura-pagar'),
    path('loja/<int:loja_id>/subscricao/mudar/',                       v.loja_subscricao_mudar, name='loja-subscricao-mudar'),
    # admin
    path('admin/planos/',                                               v.admin_planos,        name='admin-planos'),
    path('admin/planos/<int:plano_id>/',                                v.admin_plano,         name='admin-plano'),
    path('admin/subscricoes/',                                          v.admin_subscricoes,   name='admin-subscricoes'),
    path('admin/faturas/',                                              v.admin_faturas,       name='admin-faturas'),
    path('admin/faturas/<int:fatura_id>/pagar/',                        v.admin_fatura_pagar,  name='admin-fatura-pagar'),
    path('admin/lojas/<int:loja_id>/cobranca/',                         v.admin_loja_cobranca, name='admin-loja-cobranca'),
    path('admin/lojas/<int:loja_id>/subscricao/oferecer/',             v.admin_oferecer,      name='admin-oferecer'),
    path('admin/faturas/<int:fatura_id>/adiar/',                        v.admin_fatura_adiar,  name='admin-fatura-adiar'),
    path('admin/faturas/<int:fatura_id>/anular/',                       v.admin_fatura_anular, name='admin-fatura-anular'),
    path('admin/subscricoes/resumo/',                                     v.admin_resumo,        name='admin-subscricoes-resumo'),
    path('admin/subscricoes/pos/',                                      v.admin_subscricoes_pos, name='admin-subscricoes-pos'),
    path('admin/pos/<int:pos_id>/subscricao/oferecer/',                v.admin_pos_oferecer,  name='admin-pos-oferecer'),
    path('admin/pos/<int:pos_id>/subscricao/plano/',                   v.admin_pos_plano,     name='admin-pos-plano'),
]
