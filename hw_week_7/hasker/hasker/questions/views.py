from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, F, Count
from django.http import (
    HttpResponse,
    HttpRequest,
    HttpResponseRedirect,
    Http404
)
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.core.mail import send_mail

from .forms import AskQuestionForm
from .models import Question, Tag, User
from .. import settings


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

    try:
        questions_by_tag = Tag.objects.get(id=tag_id).question_set.all()
    except ObjectDoesNotExist:
        raise Http404("Tag not found")

    return render(request,
                  template_name="questions/questions.html",
                  context={"questions": questions_by_tag})


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

    try:
        question = Question.objects.get(id=question_id)
    except ObjectDoesNotExist:
        raise Http404("Вопрос не найден")

    return question


def like_question(request: HttpRequest, question_id: int) -> HttpResponse:

    question: Question = get_question(question_id)
    question.like(user=request.user)

    return HttpResponseRedirect(reverse("questions:questions"))


def dislike_question(request: HttpRequest, question_id: int) -> HttpResponse:

    question: Question = get_question(question_id)
    question.dislike(user=request.user)

    return HttpResponseRedirect(reverse("questions:questions"))


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
        from_email=settings.SERVICE_EMAIL,
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
