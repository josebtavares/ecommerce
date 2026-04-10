from django.urls import path, include
from . import views
from django.shortcuts import render

urlpatterns = [

    path('',include('app.Urls.utilizadorUrl')),
    path('', include('app.Urls.produtoUrl')),
    path('', include('app.Urls.lojaUrl')),
    path('', include('app.Urls.inventariocarrinhoencomendaUrl')),
    path('', include('app.Urls.pagamentoUrl')),
    path('',include('app.Urls.galeriaUrl')),
    path('', include('app.Urls.entregaavaliacaoUrl')),
    path('', include('app.Urls.adminUrl')),
    path('', include('app.Urls.notificacaoUrl')),
    path('', include('app.Urls.categoriadestaqueUrl'))

    
    
]