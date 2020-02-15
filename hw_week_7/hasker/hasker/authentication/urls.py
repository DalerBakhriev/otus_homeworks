from django.urls import path
from .views import LoginUserView, show_user_settings
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordChangeView
)

urlpatterns = [
    path("login/", LoginUserView.as_view(), name="login"),
    path("user_settings/", show_user_settings, name="user_settings"),
    path("password_reset/", PasswordResetView.as_view(), name="password_reset"),
    path("password_change/", PasswordChangeView.as_view(), name="password_change")
]