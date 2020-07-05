from typing import Dict

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.serializers import DateTimeField

from hasker.questions.models import Question, Answer
from hasker.users.models import User


class ViewTestCases(APITestCase):

    test_user: User
    test_question: Question
    test_answer: Answer
    test_user_credentials: Dict[str, str]

    def setUp(self):

        super().setUp()
        self.test_user_credentials = {
            "username": "test_user",
            "password": "test_password"
        }
        self.test_user = User.objects.create_user(**self.test_user_credentials)
        self.test_question = Question.objects.create(
            title="Test question title",
            text="Test question text",
            author=self.test_user
        )
        self.test_answer = self.test_question.answers.create(
            text="Test question answer",
            author=self.test_user,
            creation_date=timezone.now()
        )
        self.client.force_authenticate(user=self.test_user)

    def test_authentication(self):

        url = reverse("api:token:token_obtain_pair")
        response = self.client.post(url, self.test_user_credentials, format="json")
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_all_questions_page(self):

        url = reverse("api:questions:questions")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.test_question.id)

    def test_search_query_for_existent_question(self):

        url = f"{reverse('api:questions:search_question')}?query=question"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["id"], self.test_question.id
        )

    def test_search_query_for_non_existent_question(self):

        url = f"{reverse('api:questions:search_question')}?query=non_existent"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')
        self.assertEqual(response.data["count"], 0)

    def test_question_detail(self):

        url = reverse(
            "api:questions:question_detail", kwargs={"question_id": self.test_question.id}
        )
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')

        self.assertEqual(response.data["id"], self.test_question.id)
        self.assertEqual(response.data["title"], self.test_question.title)
        self.assertEqual(response.data["text"], self.test_question.text)
        self.assertEqual(
            response.data["author"], self.test_question.author.id
        )
        self.assertEqual(
            response.data["creation_date"],
            DateTimeField().to_representation(self.test_question.creation_date)
        )
        self.assertEqual(response.data["rating"], self.test_question.rating)
        self.assertListEqual(
            response.data["tags"],
            [tag.name for tag in self.test_question.tags.all()]
        )

