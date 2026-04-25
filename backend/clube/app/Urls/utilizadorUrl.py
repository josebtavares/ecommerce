from django.urls import path
from ..Views import utilizadorView

urlpatterns = [

    # ── Auth ──────────────────────────────────────────────────
    path('utilizador/login/',                utilizadorView.utilizador_login,          name='utilizador-login'),
    path('utilizador/registar/',             utilizadorView.utilizador_create,         name='utilizador-registar'),

    # ── Perfil do próprio utilizador ──────────────────────────
    path('utilizador/me/',                   utilizadorView.utilizador_me,             name='utilizador-me'),
    path('utilizador/me/editar/',            utilizadorView.utilizador_update_me,      name='utilizador-me-editar'),

    # ── Password reset ────────────────────────────────────────
    path('utilizador/recuperar_senha/',      utilizadorView.password_reset_request,    name='password-reset-request'),
    path('utilizador/recuperar_senha/confirmar/', utilizadorView.password_reset_confirm, name='password-reset-confirm'),

    # ── Admin da plataforma ───────────────────────────────────
    path('utilizador/',                      utilizadorView.utilizador_list,           name='utilizador-list'),
    path('utilizador/pagination/',           utilizadorView.utilizador_list_pagination,name='utilizador-list-pagination'),
    path('utilizador/<int:id>/',             utilizadorView.utilizador_get,            name='utilizador-get'),
    path('utilizador/<int:id>/eliminar/',    utilizadorView.utilizador_delete,         name='utilizador-delete'),
    path('utilizador/search/', utilizadorView.utilizador_search, name='utilizador-search'),
    
    
    #---─ Google OAuth2 ─────────────────────────────────────────────
    path('utilizador/google/',          utilizadorView.google_login_url, name='google-login-url'),
    path('utilizador/google/callback/', utilizadorView.google_callback,  name='google-callback'),
]