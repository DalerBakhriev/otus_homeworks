from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from hasker import error_handlers

urlpatterns = [
    path("", include("hasker.questions.urls")),
    path("users/", include("hasker.users.urls")),
    path("api/", include("hasker.api.urls")),
    path("admin/", admin.site.urls),
]

handler404 = error_handlers.bad_request_handler
handler500 = error_handlers.internal_server_error_handler

if settings.DEBUG:
    urlpatterns.extend(static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))
