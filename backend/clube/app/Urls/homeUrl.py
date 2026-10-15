from django.urls import path
from ..Views import homeView

urlpatterns = [
    path('home/',                          homeView.home_publica, name='home-publica'),
    path('home/seccao/<str:seccao_id>/',   homeView.home_seccao,  name='home-seccao'),
]
