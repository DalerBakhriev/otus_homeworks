from django.utils import timezone
from django.db import models
from django.urls import reverse
from ..users.models import User


class Tag(models.Model):

    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.name


class Question(models.Model):

    title = models.CharField(max_length=300)
    text = models.TextField()
    rating = models.IntegerField(default=0)
    tags = models.ManyToManyField(
        to=Tag,
        blank=True
    )
    author = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE
    )
    creation_date = models.DateTimeField(default=timezone.now)

    def get_absolute_url(self):
        return reverse("question", kwargs={'question_id': self.pk})

    @property
    def url(self):
        return self.get_absolute_url()


class Answer(models.Model):

    text = models.TextField()
    author = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE
    )
    question = models.ForeignKey(
        to=Question,
        related_name="answers",
        on_delete=models.CASCADE
    )
    creation_date = models.DateField()
    is_correct = models.BooleanField(default=False)

