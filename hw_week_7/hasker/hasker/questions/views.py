from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, redirect
from .models import Question
from django.conf import settings

from .forms import AskQuestionForm, QuestionForm


def ask_question(request: HttpRequest) -> HttpResponse:

    if request.method == 'POST':
        form = AskQuestionForm(request.POST)
        if not form.is_valid():
            return HttpResponse(f"{form.errors}")
        question_model = form.save(commit=False)
        author = request.user
        question_model.author = author
        question_model.save()
        return redirect(question_model.url)

    form = AskQuestionForm()

    return render(request, "questions/ask_question.html", {'form': form})


def show_question(request: HttpRequest, question_id: int) -> HttpResponse:

    if question_id is None:
        return HttpResponse("Could not find question id")
    question = Question.objects.get(id=question_id)
    question_form = QuestionForm(instance=question)

    return render(request,
                  template_name="questions/ask_question.html",
                  context={"form": question_form})


def show_all_questions(request: HttpRequest) -> HttpResponse:

    all_questions = Question.objects.order_by("rating", "creation_date").all()
    all_questions_for_template = list(all_questions)

    return render(request,
                  template_name="questions/questions.html",
                  context={"questions": all_questions_for_template})



