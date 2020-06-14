from django.urls import path

from . import views

app_name = "questions"
urlpatterns = [
    path("", views.QuestionListView.as_view(), name="questions"),
    path("search_question/", views.SearchQuestionListView.as_view(), name="search_question"),
    path("ask_question/", views.AskQuestionView.as_view(), name="ask_question"),
    path("tag/<int:tag_id>", views.SearchQuestionByTagListView.as_view(), name="search_question_by_tag"),
    path("question/<int:question_id>", views.QuestionDetailView.as_view(), name="question"),
    path("question/<int:question_id>/add_answer", views.add_answer, name="add_answer"),
    path("question/<int:question_id>/like", views.like_question, name="like_question"),
    path("question/<int:question_id>/dislike", views.dislike_question, name="dislike_question")
]
