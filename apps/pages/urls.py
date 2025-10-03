from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
  
    path('analytics/', views.analytics, name='analytics'),
    path('task_management/', views.task_management, name='task_management'),
    path('campaigns/', views.campaigns, name='campaigns'),
    path('profile/', views.profile, name='profile'),   # ✅ fixed here

    path('configuration/', views.configuration, name='configuration'),
    path('projects/', views.projects, name='projects'),
    path('assets/', views.assets, name='assets'),
]
