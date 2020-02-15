from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from .forms import UserSettingsForm


class LoginUserView(LoginView):

    template_name = "authentication/login.html"
    redirect_field_name = "index"
    redirect_authenticated_user = True


def show_user_settings(request: HttpRequest) -> HttpResponse:

    """
    Shows user settings form
    :param request: incoming request
    :return: renders form as response
    """

    return render(request=request,
                  template_name="authentication/user_settings.html",
                  context={"form": UserSettingsForm})


def authenticate_user(request: HttpRequest) -> HttpResponse:

    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        redirect("/index")
    else:
        return HttpResponse("Not authorized", status=401)

