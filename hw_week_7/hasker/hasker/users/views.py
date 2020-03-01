from django.contrib.auth import authenticate, login, logout
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from .forms import (
    UserSettingsForm,
    UserLoginForm,
    UserSignupForm
)
from .models import User


def authenticate_user(request: HttpRequest,
                      username: str,
                      password: str) -> HttpResponse:

    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return HttpResponseRedirect(reverse("questions:questions"))

    return HttpResponse("Not authorized", status=401)


def signup_user(request: HttpRequest) -> HttpResponse:

    if request.method == "POST":
        form = UserSignupForm(request.POST, request.FILES)
        if not form.is_valid():
            return HttpResponse(f"{form.errors}")
        user_model = form.save(commit=False)
        user_model.set_password(user_model.password)
        user_model.save()
        return HttpResponseRedirect(reverse("users:login"))

    form = UserSignupForm()

    return render(request=request,
                  template_name="users/user_signup.html",
                  context={"form": form})


def login_user(request: HttpRequest) -> HttpResponse:

    if request.method == "POST":
        return authenticate_user(
            request,
            username=request.POST["login"],
            password=request.POST["password"]
        )

    form = UserLoginForm()

    return render(request=request,
                  template_name="users/login.html",
                  context={"form": form})


def logout_user(request: HttpRequest) -> HttpResponse:
    logout(request)

    return HttpResponseRedirect(reverse("questions:questions"))


def change_user_settings(request: HttpRequest) -> HttpResponse:

    if request.method == "POST":
        user = get_object_or_404(User, id=request.user.id)
        form = UserSettingsForm(
            data=request.POST,
            files=request.FILES,
            instance=user
        )
        if not form.is_valid():
            return HttpResponse(form.errors)
        form.save(commit=True)
        return HttpResponseRedirect(redirect_to=reverse("users:login"))

    user_id = request.user.id
    user_model = User.objects.get(id=user_id)
    form = UserSettingsForm(instance=user_model)

    return render(request=request,
                  template_name="users/user_settings.html",
                  context={"form": form})


