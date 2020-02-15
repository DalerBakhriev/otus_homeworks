from django.http import HttpResponse, HttpRequest
from django.shortcuts import render

from .forms import AskQuestionForm


def ask_question(request: HttpRequest):

    """

    :param request:
    :return:
    """

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = AskQuestionForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            return HttpResponse(f"Your data is: {form.cleaned_data}")

    # if a GET (or any other method) we'll create a blank form
    else:
        form = AskQuestionForm()

    return render(request, 'questions/ask_question.html', {'form': form})
