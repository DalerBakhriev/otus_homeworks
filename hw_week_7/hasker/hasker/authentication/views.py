from django.contrib.auth import authenticate, login
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
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
        return redirect(reverse("ask_question"))

    return HttpResponse("Not authorized", status=401)


def signup_user(request: HttpRequest) -> HttpResponse:

    if request.method == "POST":
        user_model = User(
            username=request.POST["login"],
            email=request.POST["email"],
            password=request.POST["password"],
            avatar=request.POST["avatar"]
        )
        user_model.save()
        return redirect(reverse("login"))

    form = UserSignupForm()

    return render(request=request,
                  template_name="authentication/user_signup.html",
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
                  template_name="authentication/login.html",
                  context={"form": form})


def change_user_settings(request: HttpRequest) -> HttpResponse:

    if request.method == "POST":
        updated_user = User(
            username=request.POST["login"],
            email=request.POST["email"],
            avatar=request.POST["avatar"]
        )
        updated_user.save()
        return redirect(to=reverse("login"))

    user_name = request.user.username
    user_model = User.objects.get(username=user_name)
    form = UserSettingsForm(instance=user_model)

    return render(request=request,
                  template_name="authentication/user_settings.html",
                  context={"form": form})


