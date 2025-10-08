# apps/pages/api_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import TaskViewSet

router = DefaultRouter()
router.register(r"tasks", TaskViewSet, basename="tasks")

urlpatterns = [
    path("", include(router.urls)),
]
