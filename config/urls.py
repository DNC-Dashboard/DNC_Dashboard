# config/urls.py
from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("admin/", admin.site.urls),

    # your app urls
    path("api/analytics/", include("apps.analytics.urls")),
    path("charts/", include("apps.charts.urls")),
    path("api/", include("apps.dyn_api.urls")),
    path("dyn/", include("apps.dyn_dt.urls")),
    path("", include("apps.pages.urls")),

    # auth
    path("login/",  auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),  # <-- add this
]
