from datetime import timedelta
from uuid import NAMESPACE_URL, uuid5

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.models import Author, Book, BookInstance, Genre, Language


BOOKS = [
    ("Александр", "Пушкин", "Капитанская дочка", "9785170901692", "Приключения",
     "Пётр Гринёв отправляется на службу и оказывается в центре исторических событий."),
    ("Антон", "Чехов", "Вишнёвый сад", "9785171360757", "Драматургия",
     "Семья возвращается в имение и решает, можно ли спасти сад от продажи."),
    ("Николай", "Гоголь", "Мёртвые души", "9785170900350", "Роман",
     "Чичиков путешествует по губернии и знакомится с местными помещиками."),
    ("Иван", "Тургенев", "Отцы и дети", "9785170900954", "Роман",
     "Встреча молодых людей со старшим поколением оборачивается спором о взглядах и привычках."),
    ("Лев", "Толстой", "Хаджи-Мурат", "9785171371692", "Историческая проза",
     "Повесть о горском воине и его судьбе во время Кавказской войны."),
    ("Фёдор", "Достоевский", "Белые ночи", "9785171458195", "Повесть",
     "Одинокий мечтатель встречает Настеньку на петербургской набережной."),
    ("Михаил", "Лермонтов", "Герой нашего времени", "9785170900602", "Роман",
     "Несколько историй раскрывают характер Григория Печорина."),
]


class Command(BaseCommand):
    help = "Заполняет учебный каталог и при необходимости назначает демонстрационные роли."

    def add_arguments(self, parser):
        parser.add_argument("--reader", help="Имя существующего пользователя для примера выдачи.")
        parser.add_argument("--librarian", help="Имя существующего пользователя для группы библиотекарей.")

    @transaction.atomic
    def handle(self, *args, **options):
        user_model = get_user_model()
        accounts = {}
        for kind in ("reader", "librarian"):
            if options[kind]:
                try:
                    accounts[kind] = user_model.objects.get(username=options[kind])
                except user_model.DoesNotExist as exc:
                    raise CommandError(f"Пользователь {options[kind]} не найден.") from exc

        language, _ = Language.objects.get_or_create(name="Русский")
        for first, last, title, isbn, genre_name, summary in BOOKS:
            author, _ = Author.objects.get_or_create(first_name=first, last_name=last)
            genre, _ = Genre.objects.get_or_create(name=genre_name)
            book, created = Book.objects.get_or_create(isbn=isbn, defaults={
                "author": author, "title": title, "summary": summary, "language": language,
            })
            if created:
                book.genre.add(genre)
            BookInstance.objects.get_or_create(id=uuid5(NAMESPACE_URL, f"locallibrary:{isbn}:available"), defaults={
                "book": book, "imprint": "Учебный экземпляр", "status": BookInstance.Status.AVAILABLE,
            })

        if "reader" in accounts:
            book = Book.objects.get(isbn=BOOKS[0][3])
            reader = accounts["reader"]
            BookInstance.objects.get_or_create(id=uuid5(NAMESPACE_URL, f"locallibrary:loan:{reader.pk}"), defaults={
                "book": book, "imprint": "Учебный экземпляр для выдачи", "borrower": reader,
                "status": BookInstance.Status.ON_LOAN, "due_back": timezone.localdate() + timedelta(days=10),
            })
        if "librarian" in accounts:
            group, _ = Group.objects.get_or_create(name="Библиотекари")
            group.permissions.add(*Permission.objects.filter(
                content_type__app_label="catalog",
                codename__in=["can_mark_returned", "add_author", "change_author", "delete_author",
                              "add_book", "change_book", "delete_book"],
            ))
            accounts["librarian"].groups.add(group)
        self.stdout.write(self.style.SUCCESS("Учебный каталог готов."))
