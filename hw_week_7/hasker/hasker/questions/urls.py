from django.urls import path
from . import views

app_name = "questions"
urlpatterns = [
    path("", views.index, name="questions"),
    path("search_question/", views.search_question, name="search_question"),
    path("ask_question/", views.ask_question, name="ask_question"),
    path("tag/<int:tag_id>", views.search_question_by_tag, name="search_question_by_tag"),
    path("question/<int:question_id>", views.question_detail, name="question"),
    path("question/<int:question_id>/add_answer", views.add_answer, name="add_answer")
]
