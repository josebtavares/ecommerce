from django.urls import path
from ..Views import notificacaoView

urlpatterns = [
    path('notificacoes/',                               notificacaoView.notificacao_list,            name='notificacao-list'),
    path('notificacoes/contador/',                      notificacaoView.notificacao_contador,        name='notificacao-contador'),
    path('notificacoes/todas-lidas/',                   notificacaoView.notificacao_marcar_todas_lidas, name='notificacao-todas-lidas'),
    path('notificacoes/<int:notificacao_id>/lida/',     notificacaoView.notificacao_marcar_lida,     name='notificacao-lida'),
    path('notificacoes/<int:notificacao_id>/apagar/',   notificacaoView.notificacao_apagar,          name='notificacao-apagar'),
]