from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy

from .forms import (
    UserSettingsForm,
    UserLoginForm,
    UserSignupForm
)


class SignupView(CreateView):

    form_class = UserSignupForm
    template_name = "users/user_signup.html"
    success_url = reverse_lazy("users:login")


class MyLoginView(LoginView):

    form_class = UserLoginForm
    template_name = "users/login.html"
    next = reverse_lazy("questions:questions")


class MyLogoutView(LogoutView):
    next = reverse_lazy("questions:questions")


class UserEditView(LoginRequiredMixin, UpdateView):
    form_class = UserSettingsForm
    template_name = "users/user_settings.html"
    success_url = reverse_lazy("users:login")


