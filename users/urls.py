from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.contrib.auth import views as auth_views
from . import views

app_name = "users"

router = DefaultRouter()
router.register(r"users", views.UserViewSet)

urlpatterns = [
    # API endpoints
    path("api/", include(router.urls)),
    # Authentication URLs
    path(
        "login/",
        views.CustomLoginView.as_view(template_name="users/login.html"),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="medical_lab:home"),
        name="logout",
    ),
    path("register/", views.register, name="register"),
]
