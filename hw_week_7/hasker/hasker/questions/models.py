from django.db import models
from ..authentication.models import User


class Tag(models.Model):

    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.name


class Question(models.Model):

    title = models.CharField(max_length=300)
    text = models.TextField()
    rating = models.IntegerField()
    tags = models.ManyToManyField(
        to=Tag,
        blank=True
    )
    author = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE
    )
    creation_date = models.DateField()


class Answer(models.Model):

    text = models.TextField()
    author = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE
    )
    creation_date = models.DateField()
    is_correct = models.BooleanField()

