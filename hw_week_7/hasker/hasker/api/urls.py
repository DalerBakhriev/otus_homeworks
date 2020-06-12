from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from rest_framework_swagger.views import get_swagger_view

from . import views

app_name = "api"

token_patterns = ([
    path("", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("verify/", TokenVerifyView.as_view(), name="token_verify")
], "token")

question_patterns = ([
    path("", views.QuestionsListView.as_view(), name="questions"),
    path("hot/", views.HotQuestionsListView.as_view(), name="hot_questions"),
    path("search_question/", views.SearchQuestionListView.as_view(), name="search_question"),
    path("<int:question_id>/", views.QuestionDetailView.as_view(), name="question_detail"),
    path("<int:question_id>/answers", views.AnswersListView.as_view(), name="answers")
], "question")

swagger_view = get_swagger_view(title="Hasker Rest API")

url_patterns = [
    path("token/", include(token_patterns)),
    path("questions/", include(question_patterns)),
    path("schema/", swagger_view)
]
