from django.urls import path

from ..Views import favoritoView as v

urlpatterns = [
    path('favoritos/',                                 v.favoritos,        name='favoritos'),
    path('favoritos/ids/',                             v.favoritos_ids,    name='favoritos-ids'),
    path('favoritos/<str:tipo>/<int:alvo_id>/',        v.favorito_remover, name='favorito-remover'),
]
