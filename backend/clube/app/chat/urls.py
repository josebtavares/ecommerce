from django.urls import path

from . import views

urlpatterns = [
    path('caixas/',                                  views.caixas,            name='chat_caixas'),
    path('conversas/',                               views.conversas,         name='chat_conversas'),
    path('conversas/<int:conversa_id>/',             views.conversa_detalhe,  name='chat_conversa'),
    path('conversas/<int:conversa_id>/mensagens/',   views.mensagens,         name='chat_mensagens'),
    path('conversas/<int:conversa_id>/lida/',        views.marcar_lida,       name='chat_lida'),
    path('conversas/<int:conversa_id>/preferencias/', views.preferencias,     name='chat_preferencias'),
    path('conversas/<int:conversa_id>/estado/',      views.estado_conversa,   name='chat_estado'),
    path('conversas/<int:conversa_id>/bloquear/',    views.bloquear,          name='chat_bloquear'),
    path('mensagens/<int:mensagem_id>/apagar/',      views.apagar_mensagem,   name='chat_apagar'),
    path('contactos/',                               views.contactos,         name='chat_contactos'),
    path('denuncias/',                               views.denuncias,         name='chat_denuncias'),
    path('denuncias/<int:denuncia_id>/resolver/',    views.resolver_denuncia, name='chat_resolver'),
]
