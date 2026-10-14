from django.urls import path, include
from . import views
from django.shortcuts import render

urlpatterns = [

    path('',include('app.Urls.utilizadorUrl')),
    path('', include('app.Urls.produtoUrl')),
    path('', include('app.Urls.lojaUrl')),
    path('', include('app.Urls.inventariocarrinhoencomendaUrl')),
    path('', include('app.Urls.pagamentoUrl')),
    # galeria (projeto antigo): sem uso no site e as rotas aceitavam criar/editar sem login e
    # apagar itens de outros — desligadas. O modelo fica (o worker de vídeo ainda o conhece).
    # path('',include('app.Urls.galeriaUrl')),
    path('', include('app.Urls.entregaavaliacaoUrl')),
    path('', include('app.Urls.adminUrl')),
    path('', include('app.Urls.notificacaoUrl')),
    
    path('', include('app.Urls.categorialojaUrl')),
    path('', include('app.Urls.paginaUrl')),
    path('', include('app.Urls.favoritoUrl')),
    path('', include('app.Urls.subscricaoUrl')),
    

    
    
]