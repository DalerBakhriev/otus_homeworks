from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

from . import views

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
], "questions")


app_name = "api"
urlpatterns = [
    path("token/", include(token_patterns)),
    path("questions/", include(question_patterns)),
    path("docs/", views.schema_view.with_ui('swagger', cache_timeout=0)),
    path("redocs/", views.schema_view.with_ui('redoc', cache_timeout=0))
]
