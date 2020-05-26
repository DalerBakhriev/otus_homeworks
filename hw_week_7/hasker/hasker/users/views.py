from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from .models import User
from .forms import UserSettingsForm, UserSignupForm


class SignupView(CreateView):

    form_class = UserSignupForm
    template_name = "users/user_signup.html"
    success_url = reverse_lazy("users:login")


class MyLoginView(LoginView):

    template_name = "users/login.html"
    next = reverse_lazy("questions:questions")


class MyLogoutView(LogoutView):
    next = reverse_lazy("questions:questions")


class UserEditView(LoginRequiredMixin, UpdateView):

    login_url = reverse_lazy("users:login")
    permission_denied_message = "You are not logged in"
    form_class = UserSettingsForm
    model = User
    template_name = "users/user_settings.html"
    success_url = reverse_lazy("users:login")

    def get_object(self, queryset=None):
        return self.request.user


