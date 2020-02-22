from django.urls import path
from .views import ask_question, show_question


urlpatterns = [
    path("ask_question/", ask_question, name="ask_question"),
    path("question/<int:question_id>", show_question, name="question")
]
