from django.urls import path
from ..Views import pagamentoView as v

urlpatterns = [

    # ── Métodos de pagamento da loja ──────────────────────────
     path('loja/<int:loja_id>/pagamento/metodos/',
         v.metodos_loja,                         name='metodos-loja'),
     path('loja/<int:loja_id>/pagamento/metodos/<str:tipo>/',
         v.metodo_gerir,                         name='metodo-gerir'),

    # ── Pagamento (app/pagamentos: o fornecedor é o da plataforma) ──
     path('pagamento/iniciar/',               v.pagamento_iniciar,   name='pagamento-iniciar'),
     path('pagamento/regresso/',              v.pagamento_regresso,  name='pagamento-regresso'),
     path('pagamento/<slug:fornecedor>/aviso/', v.pagamento_aviso,   name='pagamento-aviso'),

    # ── Antigos (checkout aberto durante um deploy; webhook configurado no Flutterwave) ──
     path('pagamento/dinheiro/',              v.pagar_dinheiro,      name='pagar-dinheiro'),
     path('pagamento/mbway/',                 v.pagar_com_mbway,     name='pagar-mbway'),
     path('pagamento/flutterwave/verificar/', v.verificar_pagamento_flutterwave, name='flw-verificar'),
     path('pagamento/flutterwave/webhook/',   v.flutterwave_webhook, name='flw-webhook'),
]
