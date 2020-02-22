from django import forms
from .models import Question, Tag


class QuestionForm(forms.ModelForm):

    class Meta:
        model = Question
        fields = (
            "title",
            "text",
            "rating",
            "tags"
        )


class AskQuestionForm(forms.ModelForm):

    tags = forms.ModelMultipleChoiceField(
        required=False,
        to_field_name="name",
        queryset=Tag.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'multiselect'})
    )

    class Meta:
        model = Question
        fields = ("title", "text", "tags", "author")

