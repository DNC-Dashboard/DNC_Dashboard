from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
  
    path('task_management/', views.task_management, name='task_management'),
    path('analytics/', views.analytics, name='analytics')
]
