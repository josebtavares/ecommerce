from django.urls import path

from . import views as v
from . import views_backoffice as b
from . import views_cliente as c

L = 'loja/<int:loja_id>/servicos/'

urlpatterns = [
    path(L,                                         v.servicos_estado,    name='servicos-estado'),
    path(L + 'ativar/',                             v.servicos_ativar,    name='servicos-ativar'),
    path(L + 'desativar/',                          v.servicos_desativar, name='servicos-desativar'),
    path(L + 'config/',                             v.servicos_config,    name='servicos-config'),
    path(L + 'plano/',                              v.servicos_plano,     name='servicos-plano'),
    # etapa 2 — backoffice
    path(L + 'catalogo/',                           b.catalogo,               name='servicos-catalogo'),
    path(L + 'catalogo/<int:servico_id>/',          b.catalogo_item,          name='servicos-catalogo-item'),
    path(L + 'catalogo/<int:servico_id>/imagens/',  b.catalogo_imagem,        name='servicos-catalogo-imagem'),
    path(L + 'imagens/<int:imagem_id>/',            b.catalogo_imagem_apagar, name='servicos-imagem-apagar'),
    path(L + 'profissionais/',                      b.profissionais,          name='servicos-profissionais'),
    path(L + 'profissionais/<int:prof_id>/',        b.profissional,           name='servicos-profissional'),
    path(L + 'profissionais/<int:prof_id>/foto/',   b.profissional_foto,      name='servicos-profissional-foto'),
    path(L + 'profissionais/<int:prof_id>/horario/', b.profissional_horario,  name='servicos-profissional-horario'),
    path(L + 'profissionais/<int:prof_id>/ausencias/', b.ausencias,           name='servicos-ausencias'),
    path(L + 'ausencias/<int:ausencia_id>/',        b.ausencia_apagar,        name='servicos-ausencia-apagar'),
    path(L + 'agenda/',                             b.agenda_ver,             name='servicos-agenda'),
    path(L + 'disponibilidade/',                    b.disponibilidade,        name='servicos-disponibilidade'),
    path(L + 'marcacoes/',                          b.marcacoes,              name='servicos-marcacoes'),
    path(L + 'marcacoes/<int:marcacao_id>/',        b.marcacao_ver,           name='servicos-marcacao'),
    path(L + 'marcacoes/<int:marcacao_id>/acao/',   b.marcacao_acao,          name='servicos-marcacao-acao'),
    path(L + 'marcacoes/<int:marcacao_id>/livres/', b.livres_para_reatribuir, name='servicos-marcacao-livres'),
    # etapa 3 — cliente (e a conversa, que serve os dois lados)
    path('lojas/<int:loja_id>/servicos/publico/',   c.publico,     name='servicos-publico'),
    path('lojas/<int:loja_id>/servicos/horas/',     c.horas,       name='servicos-horas'),
    path('lojas/<int:loja_id>/servicos/marcar/',    c.marcar,      name='servicos-marcar'),
    path('marcacoes/',                              c.minhas,      name='marcacoes-minhas'),
    path('marcacoes/<int:marcacao_id>/',            c.minha,       name='marcacoes-minha'),
    path('marcacoes/<int:marcacao_id>/acao/',       c.minha_acao,  name='marcacoes-minha-acao'),
    path('marcacoes/<int:marcacao_id>/mensagens/',  c.mensagens,   name='marcacoes-mensagens'),
    path('marcacoes/fotos/<int:foto_id>/',          c.foto,        name='marcacoes-foto'),
]
