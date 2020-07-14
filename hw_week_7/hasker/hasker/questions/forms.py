from django import forms
from .models import Question, Tag


class QuestionForm(forms.ModelForm):

    answer = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Question
        fields = (
            "title", "text", "author",
            "tags", "answer"
        )
        widgets = {"rating": forms.NumberInput}
        labels = {
            'author': "Asked by"
        }


class AskQuestionForm(forms.ModelForm):

    tags = forms.ModelMultipleChoiceField(
        required=False,
        to_field_name="name",
        queryset=Tag.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'multiselect'})
    )

    class Meta:
        model = Question
        fields = ("title", "text", "tags")


class TagForm(forms.ModelForm):

    name = forms.CharField(max_length=100)

    class Meta:
        model = Tag
        fields = ("name",)
