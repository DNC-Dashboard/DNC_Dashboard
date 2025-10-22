# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views

from django.http import JsonResponse

def health_view(_request):
    return JsonResponse({"status": "ok"})


# --- Alias the auth namespace used by templates ---
auth_patterns = [
    # Point both to your Configuration page (where you handle password change)
    path('password_change/', RedirectView.as_view(pattern_name='configuration'),
         name='password_change'),
    path('password_change/done/', RedirectView.as_view(pattern_name='configuration'),
         name='password_change_done'),
]

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    path("health/", health_view, name="health"),
    path('api/', include('apps.tasks.urls')),



    # Auth
    path('login/',  auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Register the 'auth' namespace correctly (list + app_name + namespace)
    path('', include((auth_patterns, 'auth'), namespace='auth')),

    # Your apps
    path('', include('apps.pages.urls')),
    path('dyn/', include('apps.dyn_dt.urls')),
    path('api/', include('apps.dyn_api.urls')),
    path('api/', include('apps.pages.api_urls')),
    path('charts/', include('apps.charts.urls')),
]