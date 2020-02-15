from django import forms
from .models import User


class UserLoginForm(forms.Form):

    login = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)


class UserSettingsForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ("login", "email", "avatar")

    login = forms.CharField(max_length=100)
    email = forms.EmailField(max_length=100)
    avatar = forms.ImageField()


class UserSignupForm(forms.Form):

    login = forms.CharField(max_length=100)
    email = forms.EmailField(max_length=100)
    password = forms.CharField(max_length=100, widget=forms.PasswordInput)
    repeat_password = forms.CharField(max_length=100, widget=forms.PasswordInput)
    avatar = forms.ImageField(required=False)

