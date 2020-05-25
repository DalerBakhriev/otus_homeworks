from django.urls import path
from . import views
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordChangeView
)

app_name = "users"
urlpatterns = [
    path("signup/", views.signup_user, name="signup"),
    path("login/", views.MyLoginView.as_view(), name="login"),
    path("logout/", views.MyLogoutView.as_view(), name="logout"),
    path("user_settings/", views.UserEditView.as_view(), name="user_settings"),
    path("password_reset/", PasswordResetView.as_view(), name="password_reset"),
    path("password_change/", PasswordChangeView.as_view(), name="password_change")
]