from django.urls import path
from ..Views import inventariocarrinhoencomendaView as v

urlpatterns = [

    # ── Inventário (backoffice) ───────────────────────────────
    # GET  → inventario_list
    # POST → inventario_criar_ou_atualizar
    path('loja/<int:loja_id>/inventario/',
         v.inventario_list_ou_criar,             name='inventario-list-criar'),

    path('loja/<int:loja_id>/inventario/<int:produto_id>/ajustar/',
         v.inventario_ajustar_stock,             name='inventario-ajustar'),

    # ── Carrinho (comprador) ──────────────────────────────────
    path('loja/<int:loja_id>/carrinho/',
         v.carrinho_get,                         name='carrinho-get'),

    path('loja/<int:loja_id>/carrinho/adicionar/',
         v.carrinho_adicionar,                   name='carrinho-adicionar'),

    path('loja/<int:loja_id>/carrinho/item/<int:item_id>/',
         v.carrinho_atualizar_item,              name='carrinho-item-update'),

    path('loja/<int:loja_id>/carrinho/limpar/',
         v.carrinho_limpar,                      name='carrinho-limpar'),

    path('carrinho/',
         v.carrinho_list_utilizador,             name='carrinho-list-utilizador'),

    # ── Encomenda — comprador ─────────────────────────────────
    path('loja/<int:loja_id>/encomenda/criar/',
         v.encomenda_criar,                      name='encomenda-criar'),

    path('encomenda/',
         v.encomenda_list_comprador,             name='encomenda-list-comprador'),

    path('encomenda/<int:id>/',
         v.encomenda_get,                        name='encomenda-get'),

    # ── Encomenda — backoffice da loja ────────────────────────
    path('loja/<int:loja_id>/encomendas/',
         v.encomenda_list_loja,                  name='encomenda-list-loja'),

    path('loja/<int:loja_id>/encomendas/<int:id>/status/',
         v.encomenda_atualizar_status,           name='encomenda-status'),
]