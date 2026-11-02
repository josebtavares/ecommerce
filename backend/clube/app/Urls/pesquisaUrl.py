from django.urls import path

from ..Views import pesquisaView as v

urlpatterns = [
    path('pesquisa/', v.pesquisa, name='pesquisa'),
    path('pesquisa/registo/', v.pesquisa_registo, name='pesquisa-registo'),
    path('admin/pesquisas/', v.admin_pesquisas, name='admin-pesquisas'),
]
