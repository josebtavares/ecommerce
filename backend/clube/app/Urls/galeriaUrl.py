from django.urls import path
from ..Views import galeriaView
from django.shortcuts import render

urlpatterns = [
   
    path('galeria/', galeriaView.galeria_list),
    path('galeria/<int:id>/',galeriaView.galeria_get),
    path('galeria/registar/',galeriaView.galeria_create),
    path('galeria/editar/<int:id>/',galeriaView.galeria_update),
    path('galeria/eliminar/<int:id>/',galeriaView.galeria_delete),
    path('galeria/utilizador/<int:utilizador_id>/', galeriaView.galeria_list_by_utilizador),
    
]