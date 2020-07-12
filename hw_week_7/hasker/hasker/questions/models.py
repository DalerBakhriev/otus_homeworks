from typing import Union

from django.conf import settings
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone

from hasker.users.models import User


class Tag(models.Model):

    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.name


class SimpleAction(models.IntegerChoices):

    LIKE = 1
    DISLIKE = -1


class AbstractQuestionAnswer(models.Model):

    class Meta:
        abstract = True

    text = models.TextField()
    creation_date = models.DateTimeField(default=timezone.now)

    @transaction.atomic
    def make_user_action(self, user: User, action: SimpleAction) -> None:
        make_user_action_(action_object=self, user=user, action=action)

    @property
    def rating(self):
        rating_aggregation_result = self.actions.aggregate(rating=models.Sum("action"))["rating"]
        rating = rating_aggregation_result if rating_aggregation_result is not None else 0
        return rating


class Question(AbstractQuestionAnswer):

    author = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        related_name="questions",
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=300)

    tags = models.ManyToManyField(
        to=Tag,
        blank=True
    )

    def get_absolute_url(self):
        return reverse("questions:question", kwargs={'question_id': self.pk})

    @property
    def url(self):
        return self.get_absolute_url()


class Answer(AbstractQuestionAnswer):

    author = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        related_name="answers",
        on_delete=models.CASCADE
    )
    question = models.ForeignKey(
        to=Question,
        related_name="answers",
        on_delete=models.CASCADE
    )
    is_correct = models.BooleanField(default=False)


class AbstractUserAction(models.Model):

    action = models.IntegerField(choices=SimpleAction.choices)
    action_date = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True


class QuestionAction(AbstractUserAction):

    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        related_name="question_actions",
        on_delete=models.CASCADE
    )
    question = models.ForeignKey(
        to=Question,
        related_name="actions",
        on_delete=models.CASCADE
    )


class AnswerAction(AbstractUserAction):

    user = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        related_name="answer_actions",
        on_delete=models.CASCADE
    )
    answer = models.ForeignKey(
        to=Answer,
        related_name="actions",
        on_delete=models.CASCADE
    )


def make_user_action_(action_object: Union[Question, Answer],
                      user: User,
                      action: SimpleAction) -> None:

    """
    Makes action (like or dislike) on object (question or answer
    :param action_object: object to maker action on (concrete question or answer)
    :param user: user who makes action
    :param action: action that should be made (like or dislike)
    """

    opposite_action = SimpleAction.DISLIKE if action == SimpleAction.LIKE else SimpleAction.LIKE
    action_object.actions.filter(
        models.Q(user_id=user.id) &
        models.Q(action=opposite_action)
    ).delete()

    user_action_is_already_done = action_object.actions.filter(
        models.Q(user_id=user.id) &
        models.Q(action=action)
    )

    if user_action_is_already_done.exists():
        user_action_is_already_done.delete()
        return

    action_object.actions.create(
        user_id=user.id,
        action=action
    )
