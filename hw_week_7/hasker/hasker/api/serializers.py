from rest_framework import serializers
from hasker.questions.models import Question, Answer


class QuestionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Question
        fields = ("id", "title", "text", "author",
                  "creation_date", "tags", "rating")


class AnswerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Answer
        fields = ("text", "author", "question",
                  "creation_date", "is_correct")

