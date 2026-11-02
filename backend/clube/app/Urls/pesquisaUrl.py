from django.urls import path

from ..Views import pesquisaView as v

urlpatterns = [
    path('pesquisa/', v.pesquisa, name='pesquisa'),
]
