import os

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    avatar = models.ImageField(
        upload_to="avatars",
        null=True,
        blank=True
    )

    def __str__(self) -> str:
        return self.username

    def get_avatar_url(self):
        default_avatar_url = os.path.join(settings.STATIC_URL, "img/default_avatar.jpg")
        return self.avatar.url if self.avatar else default_avatar_url



