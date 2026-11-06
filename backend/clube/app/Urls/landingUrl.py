from django.urls import path
from ..Views import landingView as V

urlpatterns = [
    path('landing/',                                          V.landing_publica,          name='landing-publica'),
    path('admin/landing/',                                    V.admin_landing,            name='admin-landing'),
    path('admin/landing/seccoes/<str:tipo>/',                 V.admin_landing_seccao,     name='admin-landing-seccao'),
    path('admin/landing/ordem/',                              V.admin_landing_ordem,      name='admin-landing-ordem'),
    path('admin/landing/publicar/',                           V.admin_landing_publicar,   name='admin-landing-publicar'),
    path('admin/landing/descartar/',                          V.admin_landing_descartar,  name='admin-landing-descartar'),
    path('admin/landing/padrao/',                             V.admin_landing_padrao,     name='admin-landing-padrao'),
    path('admin/landing/publicacoes/',                        V.admin_landing_publicacoes, name='admin-landing-publicacoes'),
    path('admin/landing/publicacoes/<int:pub_id>/restaurar/', V.admin_landing_restaurar,  name='admin-landing-restaurar'),
    path('admin/landing/youtube/',                            V.admin_landing_youtube,    name='admin-landing-youtube'),
]
