# apps/analytics/urls.py
from django.urls import path
from .views import traffic_api

urlpatterns = [
    path("traffic", traffic_api, name="traffic_api"),
    path("traffic/<int:days>", traffic_api, name="traffic_api_days"),
]
