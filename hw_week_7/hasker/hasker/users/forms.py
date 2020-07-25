from django import forms
from .models import User
from django.utils.translation import gettext_lazy
from django.core.exceptions import ValidationError


class UserSettingsForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ("username", "email", "avatar")
        labels = {
            'username': gettext_lazy('login')
        }


class UserSignupForm(forms.ModelForm):

    repeat_password = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ("username", "email", "password", "avatar")
        labels = {'username': 'login'}
        widgets = {"password": forms.PasswordInput}

    field_order = ["username", "email", "password", "repeat_password", "avatar"]

    def clean(self):
        cleaned_data = super().clean()
        # validate that passwords match
        password = cleaned_data.get("password")
        repeated_password = cleaned_data.get("repeat_password")

        if password != repeated_password:
            raise ValidationError("Passwords don't match")
