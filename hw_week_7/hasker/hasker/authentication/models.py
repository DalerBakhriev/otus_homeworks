from datetime import datetime, timedelta
from typing import Optional

import jwt
from django.conf import settings
from django.contrib.auth.models import (
    AbstractUser,
    BaseUserManager
)
from django.db import models


class User(AbstractUser):

    avatar = models.ImageField(
        upload_to="pictures/",
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


class UserManager(BaseUserManager):

    """
    Django requires that custom users define their own Manager class. By
    inheriting from `BaseUserManager`, we get a lot of the same code used by
    Django to create a `User` for free.
    All we have to do is override the `create_user` function which we will use
    to create `User` objects.
    """

    def create_user(self,
                    username: Optional[str],
                    email: Optional[str],
                    password: Optional[str] = None) -> User:

        """
        Create and return a `User` with an email,
        username, password and avatar.
        """

        if username is None:
            raise TypeError('Users must have a username.')

        if email is None:
            raise TypeError('Users must have an email address.')

        user = self.model(username=username, email=self.normalize_email(email))
        user.set_password(password)
        user.save()

        return user



