from pathlib import Path

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone

from .models import DesignRequest, User


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


class DesignRequestForm(forms.ModelForm):
    class Meta:
        model = DesignRequest
        fields = ("title", "description", "category", "photo")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "photo": forms.ClearableFileInput(attrs={"accept": ".jpg,.jpeg,.png,.bmp"}),
        }
        help_texts = {"photo": "JPG, JPEG, PNG или BMP. Максимальный размер — 2 МБ."}

    def clean_photo(self):
        photo = self.cleaned_data["photo"]
        if photo.size > 2 * 1024 * 1024:
            raise forms.ValidationError("Размер файла не должен превышать 2 МБ.")
        formats = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".bmp": "BMP"}
        if formats.get(Path(photo.name).suffix.lower()) != photo.image.format:
            raise forms.ValidationError("Загрузите изображение в формате JPG, JPEG, PNG или BMP.")
        return photo


class RequestStatusForm(forms.Form):
    status = forms.ChoiceField(label="Новый статус", choices=[
        ("", "Выберите статус"),
        (DesignRequest.Status.ACCEPTED, DesignRequest.Status.ACCEPTED.label),
        (DesignRequest.Status.COMPLETED, DesignRequest.Status.COMPLETED.label),
    ])
    comment = forms.CharField(label="Комментарий", required=False, widget=forms.Textarea(attrs={"rows": 4}))
    design = forms.ImageField(label="Готовый дизайн", required=False)

    def clean(self):
        data = super().clean()
        status = data.get("status")
        if status == DesignRequest.Status.ACCEPTED and not data.get("comment"):
            self.add_error("comment", "Напишите комментарий для принятия заявки в работу.")
        if status == DesignRequest.Status.COMPLETED and "design" in data and not data["design"]:
            self.add_error("design", "Прикрепите изображение готового дизайна.")
        return data
