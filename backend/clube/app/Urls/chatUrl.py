# chat/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from app.Views.chatView import ThreadViewSet

router = DefaultRouter()
router.register(r"threads", ThreadViewSet, basename="chat-thread")

urlpatterns = [
    path("", include(router.urls)),
]