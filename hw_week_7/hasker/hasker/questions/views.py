from django.conf import settings
from django.core.mail import send_mail
from django.views.generic import DetailView, CreateView, ListView
from django.db.models import Q, F, Count
from django.db.models.query import QuerySet
from django.http import (
    HttpResponse,
    HttpRequest,
    HttpResponseRedirect,
    Http404
)
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from .forms import AskQuestionForm
from .models import Question, Tag, User


class QuestionListView(ListView):

    template_name = "questions/questions.html"
    context_object_name = "questions"
    allow_empty = True
    model = Question
    paginate_by = settings.MAX_QUESTIONS_ON_PAGE
    queryset: QuerySet

    def get_queryset(self):

        questions = self.model.objects.annotate(
            likes=Count("users_who_liked"),
            dislikes=Count("users_who_disliked"),
        ).order_by(F("dislikes") - F("likes"), "-creation_date")

        return questions


def index(request: HttpRequest) -> HttpResponse:

    questions = Question.objects.annotate(
        likes=Count("users_who_liked"),
        dislikes=Count("users_who_disliked"),
    ).order_by(F("dislikes") - F("likes"), "-creation_date")[:settings.MAX_QUESTIONS_ON_PAGE]

    return render(request,
                  template_name="questions/questions.html",
                  context={"questions": questions})


def search_question(request: HttpRequest) -> HttpResponse:

    query = request.POST["query"]
    questions_for_query = Question.objects.filter(
        Q(title__icontains=query) | Q(text__icontains=query)
    ).annotate(
        likes=Count("users_who_liked"),
        dislikes=Count("users_who_disliked"),
    ).order_by(F("dislikes") - F("likes"), "-creation_date")[:settings.MAX_QUESTIONS_ON_PAGE]

    return render(request,
                  template_name="questions/questions.html",
                  context={"questions": questions_for_query})


def search_question_by_tag(request: HttpRequest, tag_id: int) -> HttpResponse:

    questions_by_tag = get_object_or_404(Tag, id=tag_id).question_set.all()

    return render(request,
                  template_name="questions/questions.html",
                  context={"questions": questions_by_tag})


class AskQuestionView(CreateView):

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


def ask_question(request: HttpRequest) -> HttpResponse:

    if request.method == 'POST':
        form = AskQuestionForm(request.POST)
        if not form.is_valid():
            raise Http404(f"{form.errors}")
        question_model = form.save(commit=False)
        author = request.user
        question_model.author = author
        question_model.save()
        return HttpResponseRedirect(question_model.url)

    form = AskQuestionForm()

    return render(request, "questions/ask_question.html", {'form': form})


def get_question(question_id: int) -> Question:

    question = get_object_or_404(Question, id=question_id)

    return question


def like_question(request: HttpRequest, question_id: int) -> HttpResponse:

    question: Question = get_question(question_id)
    question.like(user=request.user)

    return HttpResponseRedirect(reverse("questions:questions"))


def dislike_question(request: HttpRequest, question_id: int) -> HttpResponse:

    question: Question = get_question(question_id)
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


def question_detail(request: HttpRequest, question_id: int) -> HttpResponse:

    if question_id is None:
        return Http404("Could not find question id")

    question: Question = get_question(question_id)
    answers = question.answers.order_by("-is_correct", "-creation_date").all()

    return render(request,
                  template_name="questions/question_detail.html",
                  context={"question": question,
                           "answers": answers})


def notify_question_author(user: User, question: Question) -> None:

    send_mail(
        subject="Hasker: new answer.",
        message=f"Received new answer from user {user.username}\n"
                f"Here is link for question: {question.url}",
        from_email=settings.EMAIL_HOST_PASSWORD,
        recipient_list=[question.author.email],
        fail_silently=True
    )


def add_answer(request: HttpRequest, question_id: int) -> HttpResponse:

    question: Question = get_question(question_id)
    question.answers.create(
        text=request.POST["text"],
        author=request.user,
        creation_date=timezone.now()
    )

    notify_question_author(
        user=request.user,
        question=question
    )

    return HttpResponseRedirect(reverse("questions:question", args=(question.id,)))
