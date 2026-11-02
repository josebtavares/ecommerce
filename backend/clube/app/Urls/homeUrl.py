from django.urls import path
from ..Views import homeView, publicidadeView

urlpatterns = [
    path('home/',                          homeView.home_publica, name='home-publica'),
    path('home/seccao/<str:seccao_id>/',   homeView.home_seccao,  name='home-seccao'),
    path('home/publicidade/eventos/',      publicidadeView.eventos, name='home-publicidade-eventos'),
    path('admin/estatisticas/publicidade/',     publicidadeView.admin_estatisticas,     name='admin-estat-publicidade'),
    path('admin/estatisticas/publicidade/csv/', publicidadeView.admin_estatisticas_csv, name='admin-estat-publicidade-csv'),

    path('admin/home/',                                   homeView.admin_home,                name='admin-home'),
    path('admin/home/seccoes/',                           homeView.admin_home_criar,          name='admin-home-criar'),
    path('admin/home/seccoes/<int:seccao_id>/',           homeView.admin_home_seccao,         name='admin-home-seccao'),
    path('admin/home/seccoes/<int:seccao_id>/duplicar/',  homeView.admin_home_duplicar,       name='admin-home-duplicar'),
    path('admin/home/ordem/',                             homeView.admin_home_ordem,          name='admin-home-ordem'),
    path('admin/home/publicar/',                          homeView.admin_home_publicar,       name='admin-home-publicar'),
    path('admin/home/descartar/',                         homeView.admin_home_descartar,      name='admin-home-descartar'),
    path('admin/home/padrao/',                            homeView.admin_home_padrao,         name='admin-home-padrao'),
    path('admin/home/publicacoes/',                       homeView.admin_home_publicacoes,    name='admin-home-publicacoes'),
    path('admin/home/publicacoes/<int:pub_id>/restaurar/', homeView.admin_home_restaurar,     name='admin-home-restaurar'),
    path('admin/home/imagens/',                           homeView.admin_home_imagem,         name='admin-home-imagem'),
    path('admin/home/imagens/<int:imagem_id>/',           homeView.admin_home_imagem_estado,  name='admin-home-imagem-estado'),
    path('admin/home/procurar/',                          homeView.admin_home_procurar,       name='admin-home-procurar'),
    path('admin/home/preview/',                           homeView.admin_home_preview,        name='admin-home-preview'),
    path('admin/home/preview/seccao/<str:seccao_id>/',    homeView.admin_home_preview_seccao, name='admin-home-preview-seccao'),
]
