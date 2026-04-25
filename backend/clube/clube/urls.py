"""
URL configuration for clube project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from app.Views.login_token import MyTokenView


from rest_framework_simplejwt.views import (
    TokenObtainPairView,   # /token/  → devolve access+refresh
    TokenRefreshView,      # /token/refresh/
    TokenVerifyView,       # opcional
)

def trigger_error(request):
    division_by_zero = 1 / 0

urlpatterns = [
    path("api/token/", MyTokenView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/",  TokenVerifyView.as_view(),  name="token_verify"),
    path("api/chat/",  include('app.Urls.chatUrl')),  # chat/urls.py
    path('admin/', admin.site.urls),
    path('app/', include('app.urls')),
   
    # ... as tuas urls existentes ...
    path('sentry-debug/', trigger_error),

    
]

# DEBUG=True: Django fará serve directo dos uploads
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
