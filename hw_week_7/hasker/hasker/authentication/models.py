from datetime import datetime, timedelta
from typing import Optional

import jwt
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    avatar = models.ImageField(
        upload_to="imgs/",
        null=True,
        blank=True
    )

    @property
    def token(self):
        return self._generate_jwt_token()

    def _generate_jwt_token(self):

        """
        Generates a JSON Web Token that stores this user's ID and has an expiry
        date set to 60 days into the future.
        """

        dt = datetime.now() + timedelta(days=60)

        token = jwt.encode({
            'id': self.pk,
            'exp': int(dt.strftime('%s'))
        }, settings.SECRET_KEY, algorithm='HS256')

        return token.decode('utf-8')


