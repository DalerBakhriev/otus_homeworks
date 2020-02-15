from django.urls import path
from .views import login_user, change_user_settings, signup_user
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordChangeView
)

urlpatterns = [
    path("signup/", signup_user, name="signup"),
    path("login/", login_user, name="login"),
    path("user_settings/", change_user_settings, name="user_settings"),
    path("password_reset/", PasswordResetView.as_view(), name="password_reset"),
    path("password_change/", PasswordChangeView.as_view(), name="password_change")
]