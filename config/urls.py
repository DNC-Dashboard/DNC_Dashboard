# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # ---- Auth URLs ----
    # Login page at /login/ (uses your template: templates/accounts/login.html)
    path(
        'login/',
        auth_views.LoginView.as_view(template_name='accounts/login.html'),
        name='login'
    ),
    # Logout and go back to /login/
    path(
        'logout/',
        auth_views.LogoutView.as_view(next_page='login'),
        name='logout'
    ),

    # Provide names used by templates so reverse('password_change') works.
    # (We route them to your Configuration page where you handle password update.)
    path('password_change/', RedirectView.as_view(pattern_name='configuration'), name='password_change'),
    path('password_change/done/', RedirectView.as_view(pattern_name='configuration'), name='password_change_done'),

    # ---- Your apps ----
    path('', include('apps.pages.urls')),     # index, analytics, projects, assets, profile, etc.
    path('dyn/', include('apps.dyn_dt.urls')),
    path('api/', include('apps.dyn_api.urls')),
    path('charts/', include('apps.charts.urls')),
]