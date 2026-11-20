import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Genre(models.Model):
    name = models.CharField("название", max_length=120, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "жанр"
        verbose_name_plural = "жанры"

    def __str__(self):
        return self.name


class Language(models.Model):
    name = models.CharField("название", max_length=80, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "язык"
        verbose_name_plural = "языки"

    def __str__(self):
        return self.name


class Author(models.Model):
    first_name = models.CharField("имя", max_length=100)
    last_name = models.CharField("фамилия", max_length=100)
    date_of_birth = models.DateField("дата рождения", blank=True, null=True)
    date_of_death = models.DateField("дата смерти", blank=True, null=True)

    class Meta:
        ordering = ["last_name", "first_name", "pk"]
        verbose_name = "автор"
        verbose_name_plural = "авторы"

    def get_absolute_url(self):
        return reverse("author-detail", args=[self.pk])

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Book(models.Model):
    title = models.CharField("название", max_length=200)
    author = models.ForeignKey(Author, verbose_name="автор", on_delete=models.SET_NULL, null=True)
    summary = models.TextField("описание", max_length=1500)
    isbn = models.CharField("ISBN", max_length=13, unique=True)
    genre = models.ManyToManyField(Genre, verbose_name="жанры")
    language = models.ForeignKey(Language, verbose_name="язык", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["title", "pk"]
        verbose_name = "книга"
        verbose_name_plural = "книги"

    def get_absolute_url(self):
        return reverse("book-detail", args=[self.pk])

    def __str__(self):
        return self.title


class BookInstance(models.Model):
    class Status(models.TextChoices):
        MAINTENANCE = "m", "На обслуживании"
        ON_LOAN = "o", "Выдан"
        AVAILABLE = "a", "Доступен"
        RESERVED = "r", "Забронирован"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    book = models.ForeignKey(Book, verbose_name="книга", on_delete=models.CASCADE, related_name="copies")
    imprint = models.CharField("издание", max_length=200)
    due_back = models.DateField("срок возврата", blank=True, null=True)
    borrower = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="читатель", on_delete=models.SET_NULL, blank=True, null=True,
    )
    status = models.CharField("статус", max_length=1, choices=Status.choices, default=Status.MAINTENANCE)

    class Meta:
        ordering = ["due_back", "id"]
        permissions = [("can_mark_returned", "Может управлять выдачами")]
        verbose_name = "экземпляр"
        verbose_name_plural = "экземпляры"

    @property
    def is_overdue(self):
        return self.due_back is not None and self.due_back < timezone.localdate()

    def __str__(self):
        return f"{self.book} ({self.id})"
