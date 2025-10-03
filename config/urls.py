# config/urls.py
from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views

urlpatterns = [
   path('', include('apps.pages.urls')),
    path('/members', include('apps.pages.urls')),
    path('', include('apps.dyn_dt.urls')),
    path('', include('apps.dyn_api.urls')),
    path('charts/', include('apps.charts.urls')),
    path("admin/", admin.site.urls),
    path("", include('admin_adminlte.urls')),
    path('', include('apps.pages.urls')),  # handles / and /members/
    path('admin/', admin.site.urls),
    path("accounts/", include(("django.contrib.auth.urls", "auth"), namespace="auth")),

 path("login/", auth_views.LoginView. as_view(template_name="accounts/login.html"), name="login"), 
path("logout/", auth_views.LogoutView as_view(next-page="login"), name="logout"),

]
