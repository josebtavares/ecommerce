from django.urls import path, re_path
from ..Views import seoView as v

urlpatterns = [
    path('seo/loja/<int:id>/',  v.seo_pagina,  name='seo-pagina'),
    path('seo/sitemap/',        v.seo_sitemap, name='seo-sitemap'),
    re_path(r'^seo/imagem/(?P<tipo>loja|produto)/(?P<id>\d{1,12})\.jpg$', v.seo_imagem, name='seo-imagem'),
]
