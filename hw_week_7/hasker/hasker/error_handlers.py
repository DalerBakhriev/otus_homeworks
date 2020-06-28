from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def bad_request_handler(request: HttpRequest, exception: Exception) -> HttpResponse:
    return render(request, "404.html")


def internal_server_error_handler(request: HttpRequest) -> HttpResponse:
    return render(request, "500.html")
