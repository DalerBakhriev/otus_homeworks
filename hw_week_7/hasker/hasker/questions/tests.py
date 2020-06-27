from datetime import timedelta

from django.test import TestCase
from django.urls import reverse_lazy
from django.utils import timezone
from hasker.questions.models import Question
from hasker.users.models import User


def create_test_user() -> User:

    user = User.objects.create(
        username="test_user",
        password="test_password"
    )

    return user


class QuestionsListIndexTestCases(TestCase):

    questions = {}
    test_user: User

    @classmethod
    def setUpTestData(cls) -> None:

        cls.test_user = create_test_user()

        cls.questions["question_1"] = Question.objects.create(
            title="strange_test_question_title",
            text="strange_test_question_text",
            author=cls.test_user,
            creation_date=timezone.now()
        )

        cls.questions["question_2"] = Question.objects.create(
            title="usual_test_question_title",
            text="usual_test_question_text",
            author=cls.test_user,
            creation_date=timezone.now() + timedelta(days=2)
        )

        cls.questions["question_3"] = Question.objects.create(
            title="test_random_title",
            text="testing_random_text",
            author=cls.test_user,
            creation_date=timezone.now() - timedelta(days=2)
        )

    def test_sorting_by_creation_date(self):

        response = self.client.get(reverse_lazy("questions:questions"))
        self.assertListEqual(
            list(response.context["questions"]),
            [
                self.questions["question_2"],
                self.questions["question_1"],
                self.questions["question_3"]
            ]
        )

    def test_sorting_by_likes_number(self):

        self.questions["question_3"].like(user=self.test_user)
        response = self.client.get(reverse_lazy("questions:questions"))
        self.assertListEqual(
            list(response.context["questions"]),
            [
                self.questions["question_3"],
                self.questions["question_2"],
                self.questions["question_1"]
            ]
        )

    def test_searching_with_query(self):

        response = self.client.get(reverse_lazy("questions:search_question"), data={"query": "strange"})
        self.assertListEqual(
            list(response.context["questions"]),
            [self.questions["question_1"]]
        )

    def test_searching_for_nonexistent_words(self):

        response = self.client.get(reverse_lazy("questions:search_question"), data={"query": "nonexistent"})
        self.assertListEqual(
            list(response.context["questions"]),
            []
        )

    def test_searching_for_word_in_the_middle(self):

        response = self.client.get(reverse_lazy("questions:search_question"), data={"query": "random"})
        self.assertListEqual(
            list(response.context["questions"]),
            [self.questions["question_3"]]
        )

    def test_searching_for_word_in_the_middle_in_text(self):

        response = self.client.get(reverse_lazy("questions:search_question"), data={"query": "random_text"})
        self.assertListEqual(
            list(response.context["questions"]),
            [self.questions["question_3"]]
        )

    def test_searching_result_sorting(self):

        response = self.client.get(reverse_lazy("questions:search_question"), data={"query": "test"})
        self.assertListEqual(
            list(response.context["questions"]),
            [
                self.questions["question_2"],
                self.questions["question_1"],
                self.questions["question_3"]
            ]
        )
