from django.urls import path, re_path
from ..Views import seoView as v

urlpatterns = [
    path('seo/loja/<str:ref>/', v.seo_pagina,  name='seo-pagina'),
    path('seo/landing/',        v.seo_landing, name='seo-landing'),
    path('seo/sitemap/',        v.seo_sitemap, name='seo-sitemap'),
    path('seo/versao/',         v.seo_versao,  name='seo-versao'),
    re_path(r'^seo/imagem/(?P<tipo>loja|produto)/(?P<id>\d{1,12})\.jpg$', v.seo_imagem, name='seo-imagem'),
    re_path(r'^seo/imagem/landing/(?P<id>\d{1,12})\.jpg$', v.seo_imagem_landing, name='seo-imagem-landing'),
]
