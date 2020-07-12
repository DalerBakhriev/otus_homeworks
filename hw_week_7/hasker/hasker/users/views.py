from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponse
from django.shortcuts import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from .forms import UserSettingsForm, UserSignupForm
from .models import User


class SignupView(CreateView):

    object: User
    form_class = UserSignupForm
    model = User
    template_name = "users/user_signup.html"
    success_url = reverse_lazy("users:login")

    def form_valid(self, form: UserSignupForm) -> HttpResponse:

        self.object = form.save(commit=False)
        self.object.set_password(self.object.password)
        self.object.save()

        return HttpResponseRedirect(self.get_success_url())


class MyLoginView(LoginView):

    form_class = AuthenticationForm
    template_name = "users/login.html"
    next = reverse_lazy("questions:questions")


class MyLogoutView(LogoutView):
    next_page = reverse_lazy("questions:questions")


class UserEditView(LoginRequiredMixin, UpdateView):

    login_url = reverse_lazy("users:login")
    permission_denied_message = "You are not logged in"
    form_class = UserSettingsForm
    model = User
    template_name = "users/user_settings.html"
    success_url = reverse_lazy("users:login")

    def get_object(self, queryset=None):
        return self.request.user
