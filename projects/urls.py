from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    # Page view
    path('', views.projects_view, name='projects'),

    # API endpoints
    path('api/projects/', views.get_projects, name='api_get_projects'),
    path('api/projects/create/', views.create_project, name='api_create_project'),
    path('api/projects/<int:project_id>/update/', views.update_project, name='api_update_project'),
    path('api/projects/<int:project_id>/delete/', views.delete_project, name='api_delete_project'),
    path('api/staff/', views.get_staff_members, name='api_get_staff'),
    path('api/staff/<int:user_id>/', views.get_staff_by_id, name='api_get_staff_by_id'),

path('<int:project_id>/tasks/', views.tasks_view, name='tasks'),
path('api/projects/<int:project_id>/tasks/', views.get_project_tasks, name='api_get_tasks'),
path('api/projects/<int:project_id>/tasks/create/', views.create_task, name='api_create_task'),
path('api/projects/<int:project_id>/tasks/<int:task_id>/update/', views.update_task, name='api_update_task'),
path('api/projects/<int:project_id>/tasks/<int:task_id>/delete/', views.delete_task, name='api_delete_task'),


]
