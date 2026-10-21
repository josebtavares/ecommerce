from django.urls import path

from . import views as v

urlpatterns = [
    path('loja/<int:loja_id>/servicos/',            v.servicos_estado,    name='servicos-estado'),
    path('loja/<int:loja_id>/servicos/ativar/',     v.servicos_ativar,    name='servicos-ativar'),
    path('loja/<int:loja_id>/servicos/desativar/',  v.servicos_desativar, name='servicos-desativar'),
    path('loja/<int:loja_id>/servicos/config/',     v.servicos_config,    name='servicos-config'),
    path('loja/<int:loja_id>/servicos/plano/',      v.servicos_plano,     name='servicos-plano'),
]
