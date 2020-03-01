from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone

from ..users.models import User


class Tag(models.Model):

    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.name


class Question(models.Model):

    title = models.CharField(max_length=300)
    text = models.TextField()
    users_who_liked = models.ManyToManyField(User, related_name="question_likes")
    users_who_disliked = models.ManyToManyField(User, related_name="question_dislikes")

    tags = models.ManyToManyField(
        to=Tag,
        blank=True
    )
    author = models.ForeignKey(
        to=User,
        related_name="author",
        on_delete=models.CASCADE
    )
    creation_date = models.DateTimeField(default=timezone.now)

    @transaction.atomic
    def like(self, user: User) -> None:

        self.users_who_disliked.remove(user)
        if self.users_who_liked.filter(id=user.id).exists():
            self.users_who_liked.remove(user)
        else:
            self.users_who_liked.add(user)

    @transaction.atomic
    def dislike(self, user: User) -> None:

        self.users_who_liked.remove(user)
        if self.users_who_disliked.filter(id=user.id).exists():
            self.users_who_disliked.remove(user)
        else:
            self.users_who_disliked.add(user)

    @property
    def rating(self):
        return self.users_who_liked.count() - self.users_who_disliked.count()

    def get_absolute_url(self):
        return reverse("questions:question", kwargs={'question_id': self.pk})

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

