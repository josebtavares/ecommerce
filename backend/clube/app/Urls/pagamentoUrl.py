from django.urls import path
from ..Views import pagamentoView as v

urlpatterns = [

    # ── Cartões guardados ─────────────────────────────────────
     path('pagamento/cartoes/',
         v.cartao_list,                          name='cartao-list'),
     path('pagamento/cartoes/<int:id>/remover/',
         v.cartao_remover,                       name='cartao-remover'),
     path('pagamento/cartoes/<int:id>/predefinir/',
         v.cartao_predefinir,                    name='cartao-predefinir'),

    # ── Métodos de pagamento da loja ──────────────────────────
     path('loja/<int:loja_id>/pagamento/metodos/',
         v.metodos_loja,                         name='metodos-loja'),
     path('loja/<int:loja_id>/pagamento/metodos/<str:tipo>/',
         v.metodo_gerir,                         name='metodo-gerir'),

    # ── Pagamento ─────────────────────────────────────────────
     path('pagamento/cartao/',
         v.pagar_com_cartao,                     name='pagar-cartao'),
     path('pagamento/mbway/',
         v.pagar_com_mbway,                      name='pagar-mbway'),
     path('pagamento/dinheiro/',
         v.pagar_dinheiro,                       name='pagar-dinheiro'),

    # ── Stripe Webhook (não requer auth) ──────────────────────
     path('pagamento/webhook/stripe/',
         v.stripe_webhook,                       name='stripe-webhook'),
    
    # ── Flutterwave Webhook ─────────────────
     path('pagamento/flutterwave/iniciar/',   v.iniciar_pagamento_flutterwave, name='flw-iniciar'),
     path('pagamento/flutterwave/verificar/', v.verificar_pagamento_flutterwave, name='flw-verificar'),
     path('pagamento/flutterwave/webhook/',   v.flutterwave_webhook, name='flw-webhook'),
]