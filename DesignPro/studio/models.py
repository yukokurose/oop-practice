from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    username = models.CharField(
        "Логин", max_length=150, unique=True,
        validators=[RegexValidator(r"\A[A-Za-z-]+\Z", "Используйте латинские буквы и дефисы.")],
        error_messages={"unique": "Этот логин уже занят."},
    )
    full_name = models.CharField(
        "ФИО", max_length=150, blank=True,
        validators=[RegexValidator(r"\A[А-Яа-яЁё -]+\Z", "Используйте кириллицу, пробелы и дефисы.")],
    )
    consented_at = models.DateTimeField("Дата согласия", blank=True, null=True, editable=False)

    def get_full_name(self):
        return self.full_name or super().get_full_name()


class Category(models.Model):
    name = models.CharField("Категория", max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "категория"
        verbose_name_plural = "категории"

    def __str__(self):
        return self.name


class DesignRequest(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Новая"
        ACCEPTED = "accepted", "Принято в работу"
        COMPLETED = "completed", "Выполнено"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="design_requests")
    title = models.CharField("Название", max_length=150)
    description = models.TextField("Описание")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория")
    photo = models.ImageField("Фото помещения или план", upload_to="requests/")
    design = models.ImageField("Готовый дизайн", upload_to="designs/", blank=True)
    status = models.CharField("Статус", max_length=12, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField("Дата добавления", auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        verbose_name = "заявка"
        verbose_name_plural = "заявки"

    def __str__(self):
        return self.title
