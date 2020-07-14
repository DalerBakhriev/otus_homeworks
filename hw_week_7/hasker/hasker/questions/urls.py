from django.urls import path, re_path

from . import views

app_name = "questions"
urlpatterns = [
    path("", views.QuestionListView.as_view(), name="questions"),
    path("search_question/", views.SearchQuestionListView.as_view(), name="search_question"),
    path("ask_question/", views.AskQuestionView.as_view(), name="ask_question"),
    path("tag/<int:tag_id>", views.SearchQuestionByTagListView.as_view(), name="search_question_by_tag"),
    path("question/<int:question_id>", views.QuestionDetailView.as_view(), name="question"),
    path("question/<int:question_id>/add_answer", views.AddAnswerView.as_view(), name="add_answer"),
    path("create_tag", views.CreateTagView.as_view(), name="create_tag"),
    path("question/<int:question_id>/mark_answer_as_correct/<int:answer_id>",
         views.MarkCorrectAnswerView.as_view(),
         name="mark_answer_as_correct"),
    re_path(r'^question/(?P<question_id>\d+)/action/(?P<action>[+-]1)',
            views.QuestionActionView.as_view(),
            name="question_action"),
    re_path(r'^answer/(?P<answer_id>\d+)/action/(?P<action>[+-]1)',
            views.AnswerActionView.as_view(),
            name="answer_action")
]
