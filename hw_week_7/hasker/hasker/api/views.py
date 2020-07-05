from django.db.models import Count, F, Q
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import generics
from rest_framework import permissions

from . import serializers
from hasker.questions.models import Question


class QuestionsListView(generics.ListAPIView):

    serializer_class = serializers.QuestionSerializer
    queryset = Question.objects.all()


class HotQuestionsListView(generics.ListAPIView):

    serializer_class = serializers.QuestionSerializer

    def get_queryset(self):

        questions = Question.objects.annotate(
            likes=Count("users_who_liked"),
            dislikes=Count("users_who_disliked"),
        ).order_by(F("dislikes") - F("likes"), "-creation_date")

        return questions


class SearchQuestionListView(generics.ListAPIView):

    serializer_class = serializers.QuestionSerializer

    def get_queryset(self):

        query = self.request.GET.get("query")
        if query is None:
            return Question.objects.all()

        questions_for_query = Question.objects.filter(
            Q(title__icontains=query) | Q(text__icontains=query)
        ).annotate(
            likes=Count("users_who_liked"),
            dislikes=Count("users_who_disliked"),
        ).order_by(F("dislikes") - F("likes"), "-creation_date")

        return questions_for_query


class QuestionDetailView(generics.RetrieveAPIView):

    serializer_class = serializers.QuestionSerializer
    lookup_field = "id"
    lookup_url_kwarg = "question_id"
    queryset = Question.objects.all()


class AnswersListView(generics.ListAPIView):

    serializer_class = serializers.AnswerSerializer

    def get_queryset(self):

        question_id = self.kwargs.get("question_id")
        question = get_object_or_404(Question, id=question_id)

        return question.answers.all()


schema_view = get_schema_view(
   openapi.Info(
      title="Questions API",
      default_version='v1',
      description="API for questions from hasker service",
      contact=openapi.Contact(email="BakhrievDaler@yandex.ru"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)
