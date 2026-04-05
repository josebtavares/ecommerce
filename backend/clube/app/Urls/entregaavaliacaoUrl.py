from django.urls import path
from ..Views import entregaavaliacaoView as v

urlpatterns = [

    # ── Opções de entrega ─────────────────────────────────────
    path('loja/<int:loja_id>/entrega/opcoes/',
         v.opcao_entrega_list,                   name='opcao-entrega-list'),

    path('loja/<int:loja_id>/entrega/opcoes/criar/',
         v.opcao_entrega_criar,                  name='opcao-entrega-criar'),

    path('loja/<int:loja_id>/entrega/opcoes/<int:opcao_id>/',
         v.opcao_entrega_gerir,                  name='opcao-entrega-gerir'),

    # ── Condutores ────────────────────────────────────────────
    path('loja/<int:loja_id>/entrega/condutores/',
         v.condutor_list,                        name='condutor-list'),

    path('loja/<int:loja_id>/entrega/condutores/adicionar/',
         v.condutor_adicionar,                   name='condutor-adicionar'),

    path('loja/<int:loja_id>/entrega/condutores/<int:condutor_id>/remover/',
         v.condutor_remover,                     name='condutor-remover'),

    # ── Entrega por encomenda ─────────────────────────────────
    path('loja/<int:loja_id>/encomendas/<int:encomenda_id>/entrega/criar/',
         v.entrega_criar,                        name='entrega-criar'),

    path('loja/<int:loja_id>/encomendas/<int:encomenda_id>/entrega/',
         v.entrega_get,                          name='entrega-get'),

    path('loja/<int:loja_id>/encomendas/<int:encomenda_id>/entrega/atualizar/',
         v.entrega_atualizar,                    name='entrega-atualizar'),

    # ── Avaliações ────────────────────────────────────────────
    path('loja/<int:loja_id>/avaliacoes/',
         v.avaliacao_list_loja,                  name='avaliacao-list'),

    path('loja/<int:loja_id>/avaliacoes/criar/',
         v.avaliacao_criar,                      name='avaliacao-criar'),
    
    path('loja/<int:loja_id>/avaliacoes/<int:avaliacao_id>/editar/', v.avaliacao_editar),
    
    path('loja/<int:loja_id>/avaliacoes/<int:avaliacao_id>/ocultar/', v.avaliacao_ocultar),

    path('loja/<int:loja_id>/avaliacoes/<int:avaliacao_id>/apagar/',
         v.avaliacao_apagar,                     name='avaliacao-apagar'),
    
    path('loja/<int:loja_id>/avaliacoes/pode-avaliar/', v.pode_avaliar_loja),
    
    path('loja/<int:loja_id>/entrega/lista/',  v.entrega_list_loja, name='entrega-list-loja'),
]