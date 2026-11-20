from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone

from .models import User


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(label="Электронная почта", widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    consent = forms.BooleanField(label="Я согласен на обработку персональных данных")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("full_name", "username", "email", "password1", "password2", "consent")
        widgets = {"full_name": forms.TextInput(attrs={"autocomplete": "name"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["full_name"].required = True

    def clean_full_name(self):
        name = self.cleaned_data["full_name"]
        if not any(char.isalpha() for char in name):
            raise forms.ValidationError("Введите ФИО.")
        return name

    def clean_username(self):
        username = super().clean_username()
        if username and not any(char.isalpha() for char in username):
            raise forms.ValidationError("Введите логин с латинскими буквами.")
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.consented_at = timezone.now()
        if commit:
            user.save()
        return user
