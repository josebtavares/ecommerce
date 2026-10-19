from django.urls import path

from ..Views import devolucaoView as v

urlpatterns = [
    # cliente
    path('encomendas/<int:id>/reembolso/opcoes/', v.opcoes,      name='reembolso-opcoes'),
    path('encomendas/<int:id>/cancelar/',         v.cancelar,    name='encomenda-cancelar-cliente'),
    path('encomendas/<int:id>/reembolsos/',       v.pedir,       name='reembolso-pedir'),
    path('reembolsos/',                           v.meus,        name='reembolso-meus'),
    path('reembolsos/fotos/<int:id>/',            v.foto,        name='reembolso-foto'),
    path('reembolsos/<int:id>/',                  v.detalhe,     name='reembolso-detalhe'),
    path('reembolsos/<int:id>/acao/',             v.acao_cliente, name='reembolso-acao-cliente'),
    path('reembolsos/<int:id>/mensagens/',        v.nova_mensagem, name='reembolso-mensagem'),
    # loja
    path('loja/<int:loja_id>/reembolsos/',                 v.lista_loja, name='reembolso-lista-loja'),
    path('loja/<int:loja_id>/reembolsos/<int:id>/acao/',   v.acao_loja,  name='reembolso-acao-loja'),
    # Bendi
    path('admin/reembolsos/',                     v.lista_admin,   name='reembolso-lista-admin'),
    path('admin/reembolsos/<int:id>/decidir/',    v.decidir_admin, name='reembolso-decidir'),
]
