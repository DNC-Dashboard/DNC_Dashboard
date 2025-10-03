# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views

# ---- Provide an 'auth' namespace so templates like {% url 'auth:password_change' %} work ----
auth_alias_patterns = ([
    # Send both URLs to your Configuration page (you already built the UI there)
    path('password_change/', RedirectView.as_view(pattern_name='configuration'), name='password_change'),
    path('password_change/done/', RedirectView.as_view(pattern_name='configuration'), name='password_change_done'),
], 'auth')

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Login/Logout
    path('login/',  auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Register the 'auth' namespace used by your templates
    path('', include((auth_alias_patterns, 'auth'), namespace='auth')),

    # Your apps
    path('', include('apps.pages.urls')),      # index, analytics, projects, assets, profile, configuration, …
    path('dyn/', include('apps.dyn_dt.urls')),
    path('api/', include('apps.dyn_api.urls')),
    path('charts/', include('apps.charts.urls')),
]