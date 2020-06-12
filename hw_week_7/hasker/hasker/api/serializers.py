from rest_framework import serializers
from ..questions.models import Question, Answer


class QuestionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Question
        fields = ("title", "text", "author",
                  "creation_date", "tags", "rating")


class AnswerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Answer
        fields = ("text", "author", "author",
                  "question", "creation_date", "is_correct")

