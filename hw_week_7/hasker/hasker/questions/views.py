from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import (
    HttpResponse,
    HttpRequest,
    HttpResponseRedirect,
    Http404
)
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from .forms import AskQuestionForm
from .models import Question, Tag
from .. import settings


def index(request: HttpRequest) -> HttpResponse:

    questions = Question.objects.order_by("rating", "creation_date")[:settings.MAX_QUESTIONS_ON_PAGE]

    return render(request,
                  template_name="questions/questions.html",
                  context={"questions": questions})


def search_question(request: HttpRequest) -> HttpResponse:

    query = request.POST["query"]
    questions_for_query = Question.objects.filter(
        Q(title__contains=query) | Q(text__contains=query)
    ).order_by("-rating", "-creation_date")

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


def question_detail(request: HttpRequest, question_id: int) -> HttpResponse:

    if question_id is None:
        return Http404("Could not find question id")

    question: Question = get_question(question_id)
    answers = question.answers.order_by("-is_correct", "-creation_date").all()

    return render(request,
                  template_name="questions/question_detail.html",
                  context={"question": question,
                           "answers": answers})


def add_answer(request: HttpRequest, question_id: int) -> HttpResponse:

    question: Question = get_question(question_id)
    question.answers.create(
        text=request.POST["text"],
        author=request.user,
        creation_date=timezone.now()
    )

    return HttpResponseRedirect(reverse("questions:question", args=(question.id,)))
