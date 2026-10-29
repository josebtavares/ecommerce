from django.urls import path
from ..Views import documentoLojaView as v

urlpatterns = [
    # ── Loja (só o dono) ──────────────────────────────────────
    path('loja/<int:loja_id>/documentos/',                    v.loja_documentos,        name='loja-documentos'),
    path('loja/<int:loja_id>/documentos/<int:id>/',           v.loja_documento,         name='loja-documento'),
    path('loja/<int:loja_id>/documentos/<int:id>/abrir/',     v.loja_documento_abrir,   name='loja-documento-abrir'),
    # ── Admin (verificar_documentos) ──────────────────────────
    path('admin/lojas/<int:loja_id>/documentos/',             v.admin_loja_documentos,  name='admin-loja-documentos'),
    path('admin/documentos/<int:id>/',                        v.admin_documento,        name='admin-documento'),
    path('admin/documentos/<int:id>/abrir/',                  v.admin_documento_abrir,  name='admin-documento-abrir'),
    # ── Ficheiro (link assinado) ──────────────────────────────
    path('documentos/<int:id>/ficheiro/',                     v.ficheiro,               name='documento-ficheiro'),
]
