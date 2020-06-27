from django.conf import settings
from django.core.mail import send_mail
from django.views.generic import DetailView, CreateView, ListView
from django.db.models import Q, F, Count
from django.db.models.query import QuerySet
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import (
    HttpResponse,
    HttpRequest,
    HttpResponseRedirect
)
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone

from .forms import AskQuestionForm
from .models import Question, Tag, User, Answer
from django.contrib.auth.decorators import login_required


class BaseQuestionListView(ListView):

    template_name = "questions/questions.html"
    context_object_name = "questions"
    allow_empty = True
    model = Question
    paginate_by = settings.MAX_QUESTIONS_ON_PAGE
    queryset: QuerySet


class QuestionListView(BaseQuestionListView):

    def get_queryset(self):

        questions = self.model.objects.annotate(
            likes=Count("users_who_liked"),
            dislikes=Count("users_who_disliked"),
        ).order_by(F("dislikes") - F("likes"), "-creation_date")

        return questions


class SearchQuestionListView(BaseQuestionListView):

    def get_queryset(self):

        query = self.request.GET.get("query")

        if query is None:
            return Question.objects.all()

        questions_for_query = Question.objects.filter(
            Q(title__icontains=query) | Q(text__icontains=query)
        ).annotate(
            likes=Count("users_who_liked"),
            dislikes=Count("users_who_disliked"),
        ).order_by(F("dislikes") - F("likes"), "-creation_date")[:settings.MAX_QUESTIONS_ON_PAGE]

        return questions_for_query


class SearchQuestionByTagListView(BaseQuestionListView):

    def get_queryset(self):

        tag_id = self.kwargs.get("tag_id")
        questions_by_tag = get_object_or_404(Tag, id=tag_id).question_set.all()

        return questions_by_tag


class AskQuestionView(LoginRequiredMixin, CreateView):

    object: Question
    form_class = AskQuestionForm
    model = Question
    template_name = "questions/ask_question.html"

    def form_valid(self, form: AskQuestionForm) -> HttpResponse:

        self.object = form.save(commit=False)
        self.object.author = self.request.user
        self.object.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        return self.object.get_absolute_url()


@login_required(login_url=reverse_lazy("users:login"))
def like_question(request: HttpRequest, question_id: int) -> HttpResponse:

    question: Question = get_object_or_404(Question, id=question_id)
    question.like(user=request.user)

    return HttpResponseRedirect(reverse("questions:questions"))


@login_required(login_url=reverse_lazy("users:login"))
def dislike_question(request: HttpRequest, question_id: int) -> HttpResponse:

    question: Question = get_object_or_404(Question, id=question_id)
    question.dislike(user=request.user)

    return HttpResponseRedirect(reverse("questions:questions"))


class QuestionDetailView(DetailView):

    model = Question
    template_name = "questions/question_detail.html"
    pk_url_kwarg = "question_id"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        answers = self.object.answers.order_by("-is_correct", "-creation_date").all()

        context["answers"] = answers

        return context

    def get_object(self, queryset=None) -> Question:

        question_id = self.kwargs.get(self.pk_url_kwarg)
        question_object = get_object_or_404(Question, id=question_id)

        return question_object


def notify_question_author(user: User, question: Question) -> None:

    send_mail(subject="Hasker: new answer.",
              message=f"Received new answer from user {user.username}\n"
                      f"Here is link for question: {question.url}",
              from_email=settings.EMAIL_HOST_PASSWORD,
              recipient_list=[question.author.email],
              fail_silently=True)


class AddAnswerView(LoginRequiredMixin, CreateView):

    model = Answer
    pk_url_kwarg = "question_id"
    http_method_names = ["post"]
    fields = ["text"]

    def form_valid(self, form) -> HttpResponse:

        question_id = self.kwargs.get(self.pk_url_kwarg)
        question = get_object_or_404(Question, id=question_id)

        answer_text = self.request.POST["text"]

        question.answers.create(
            text=answer_text,
            author=self.request.user,
            creation_date=timezone.now()
        )

        notify_question_author(
            user=self.request.user,
            question=question
        )

        return HttpResponseRedirect(reverse("questions:question", args=(question.id,)))
