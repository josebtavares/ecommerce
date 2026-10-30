from django.urls import path
from ..Views import vinti4View as v

urlpatterns = [
    path('loja/<int:loja_id>/vinti4/',        v.loja_vinti4,        name='loja-vinti4'),
    path('admin/lojas/<int:loja_id>/vinti4/', v.admin_loja_vinti4,  name='admin-loja-vinti4'),
]
