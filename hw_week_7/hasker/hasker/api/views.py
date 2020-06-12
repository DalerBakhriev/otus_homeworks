from django.db.models import F, Count
from django.shortcuts import get_object_or_404
from rest_framework import generics

from . import serializers
from ..questions.models import Question


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

        query = self.kwargs.get("query")
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
    queryset = Question.objects.all()


class AnswersListView(generics.ListAPIView):
    serializer_class = serializers.AnswerSerializer

    def get_queryset(self):

        question_id = self.kwargs.get("question_id")
        question = get_object_or_404(Question, id=question_id)

        return question.answers.all()



