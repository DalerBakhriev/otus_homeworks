from django.urls import path
from . import views

app_name = "questions"
urlpatterns = [
    path("", views.index, name="questions"),
    path("ask_question/", views.ask_question, name="ask_question"),
    path("question/<int:question_id>", views.question_detail, name="question"),
    path("question/<int:question_id>/add_answer", views.add_answer, name="add_answer")
]
