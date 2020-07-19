from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.db.models import Q, Sum
from django.db.models.query import QuerySet
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    DetailView,
    CreateView,
    ListView,
    RedirectView
)

from .forms import AskQuestionForm, TagForm
from .models import Question, Tag, User, Answer


class BaseQuestionListView(ListView):

    template_name = "questions/questions.html"
    context_object_name = "questions"
    allow_empty = True
    model = Question
    paginate_by = settings.MAX_QUESTIONS_ON_PAGE
    queryset: QuerySet


class QuestionListView(BaseQuestionListView):

    def get_queryset(self):

        questions = self.model.objects.prefetch_related("tags").annotate(
            Sum("actions__action")
        ).order_by("-actions__action__sum", "-creation_date")

        return questions


class SearchQuestionListView(BaseQuestionListView):

    def get_queryset(self):

        query = self.request.GET.get("query")

        if query is None:
            return Question.objects.all()

        questions_for_query = Question.objects.filter(
            Q(title__icontains=query) | Q(text__icontains=query)
        ).annotate(
            Sum("actions__action"),
        ).order_by("-actions__action__sum", "-creation_date")[:settings.MAX_QUESTIONS_ON_PAGE]

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

        form.save_m2m()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        return self.object.get_absolute_url()


class BaseActionView(LoginRequiredMixin, CreateView):

    http_method_names = ["get"]

    def get_redirect_url(self) -> str:

        if issubclass(self.model, Question):
            url_for_redirect = reverse_lazy("questions:questions")

        elif issubclass(self.model, Answer):
            answer = get_object_or_404(self.model, id=int(self.kwargs.get(self.pk_url_kwarg)))
            url_for_redirect = reverse_lazy("questions:question", args=(answer.question.id,))

        else:
            raise ValueError(
                f"Wrong model instance. "
                f"Should be one of (Question, Answer), not {type(self.model)}"
            )

        return url_for_redirect

    def get(self, request, *args, **kwargs) -> HttpResponse:

        action_object_id = int(self.kwargs.get(self.pk_url_kwarg))
        action_object = get_object_or_404(self.model, id=action_object_id)
        action_object.make_user_action(
            user=self.request.user,
            action=int(self.kwargs.get("action"))
        )

        return HttpResponseRedirect(self.get_redirect_url())


class QuestionActionView(BaseActionView):

    model = Question
    pk_url_kwarg = "question_id"


class AnswerActionView(BaseActionView):

    model = Answer
    pk_url_kwarg = "answer_id"


class QuestionDetailView(DetailView):

    model = Question
    template_name = "questions/question_detail.html"
    pk_url_kwarg = "question_id"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        answers = self.object.answers.annotate(
            Sum("actions__action"),
        ).order_by("-actions__action__sum", "-creation_date").all()

        answers_for_context = []
        for answer in answers:
            if not hasattr(answer, "correct_answer_for"):
                answers_for_context.append(answer)

        question_tags = self.object.tags.all()

        context["answers"] = answers_for_context
        context["tags"] = question_tags

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


class AddAnswerView(LoginRequiredMixin, RedirectView):

    pattern_name = "questions:question"
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs) -> HttpResponse:

        question_id = kwargs["question_id"]
        question = get_object_or_404(Question, id=question_id)

        answer_text = request.POST["text"]

        question.answers.create(
            text=answer_text,
            author=request.user,
            creation_date=timezone.now()
        )

        notify_question_author(
            user=request.user,
            question=question
        )

        return super().post(request, *args, **kwargs)


class MarkCorrectAnswerView(LoginRequiredMixin, RedirectView):

    pattern_name = "questions:question"

    def get_redirect_url(self, *args, **kwargs):
        return reverse_lazy(self.pattern_name, kwargs={"question_id": kwargs["question_id"]})

    def get(self, request, *args, **kwargs) -> HttpResponse:

        question = get_object_or_404(Question, id=kwargs["question_id"])
        answer = get_object_or_404(Answer, id=kwargs["answer_id"])
        question.correct_answer = answer
        question.save()

        return super().get(request, *args, **kwargs)


class CreateTagView(LoginRequiredMixin, CreateView):

    object: Tag
    form_class = TagForm
    template_name = "questions/create_tag.html"
    http_method_names = ["get", "post"]
    success_url = reverse_lazy("questions:questions")
