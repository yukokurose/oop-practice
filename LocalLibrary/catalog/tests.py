from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import RenewBookForm
from .models import Author, Book, BookInstance


class LibraryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.reader = users.create_user("reader", "reader@example.test", "reader-test-2026")
        cls.other = users.create_user("other")
        cls.librarian = users.create_user("librarian")
        cls.librarian.user_permissions.add(*Permission.objects.filter(
            content_type__app_label="catalog",
            codename__in=["can_mark_returned", "add_author", "change_author", "delete_author",
                          "add_book", "change_book", "delete_book"],
        ))
        cls.author = Author.objects.create(first_name="Александр", last_name="Пушкин")
        cls.book = Book.objects.create(title="Тестовая книга", author=cls.author, isbn="0000000000001")
        cls.copy = BookInstance.objects.create(
            book=cls.book, borrower=cls.reader, imprint="Читательский экземпляр",
            due_back=timezone.localdate() - timedelta(days=1), status=BookInstance.Status.ON_LOAN,
        )
        cls.other_copy = BookInstance.objects.create(
            book=cls.book, borrower=cls.other, imprint="Второй экземпляр", status=BookInstance.Status.ON_LOAN,
        )
        cls.available = BookInstance.objects.create(
            book=cls.book, imprint="На полке", status=BookInstance.Status.AVAILABLE,
        )

    def test_home_uses_database_and_counts_session_visits(self):
        self.assertRedirects(self.client.get("/"), reverse("index"))
        response = self.client.get(reverse("index"))
        self.assertEqual(response.context["num_books"], 1)
        self.assertEqual(response.context["num_instances"], 3)
        self.assertEqual(response.context["num_available"], 1)
        self.assertEqual(response.context["num_visits"], 2)

    def test_public_catalog_and_detail_pages(self):
        for url in (reverse("books"), reverse("authors"), self.book.get_absolute_url(), self.author.get_absolute_url()):
            self.assertEqual(self.client.get(url).status_code, 200)
        self.assertContains(self.client.get(self.book.get_absolute_url()), "На полке")

    def test_book_list_is_paginated(self):
        for number in range(2, 9):
            Book.objects.create(title=f"Книга {number}", isbn=f"{number:013d}")
        self.assertEqual(len(self.client.get(reverse("books")).context["book_list"]), 6)
        self.assertEqual(len(self.client.get(reverse("books"), {"page": 2}).context["book_list"]), 2)

    def test_visitor_must_log_in_to_view_personal_loans(self):
        url = reverse("my-borrowed")
        self.assertRedirects(self.client.get(url), f"{reverse('login')}?next={url}")

    def test_reader_only_sees_own_active_loans(self):
        self.client.force_login(self.reader)
        response = self.client.get(reverse("my-borrowed"))
        self.assertEqual(list(response.context["loans"]), [self.copy])
        self.assertContains(response, "Просрочено")

    def test_only_librarian_sees_all_loans_and_renews(self):
        url = reverse("renew-book-librarian", args=[self.copy.pk])
        self.client.force_login(self.reader)
        self.assertEqual(self.client.get(reverse("all-borrowed")).status_code, 403)
        self.assertEqual(self.client.post(url, {"renewal_date": timezone.localdate()}).status_code, 403)
        self.client.force_login(self.librarian)
        self.assertCountEqual(self.client.get(reverse("all-borrowed")).context["loans"], [self.copy, self.other_copy])
        new_due = timezone.localdate() + timedelta(days=7)
        self.assertRedirects(self.client.post(url, {"renewal_date": new_due}), reverse("all-borrowed"))
        self.copy.refresh_from_db()
        self.assertEqual(self.copy.due_back, new_due)
        self.assertEqual(
            self.client.get(reverse("renew-book-librarian", args=[self.available.pk])).status_code, 404,
        )

    def test_renewal_date_validation(self):
        today = timezone.localdate()
        for days, expected in ((-1, False), (0, True), (28, True), (29, False)):
            with self.subTest(days=days):
                form = RenewBookForm({"renewal_date": today + timedelta(days=days)})
                self.assertEqual(form.is_valid(), expected)

    def test_author_forms_require_permissions_and_use_post_for_delete(self):
        self.client.force_login(self.reader)
        self.assertEqual(self.client.get(reverse("author_create")).status_code, 403)
        self.client.force_login(self.librarian)
        response = self.client.post(reverse("author_create"), {"first_name": "Антон", "last_name": "Чехов"})
        author = Author.objects.get(last_name="Чехов")
        self.assertRedirects(response, author.get_absolute_url())
        self.assertRedirects(
            self.client.post(reverse("author_update", args=[author.pk]), {"first_name": "Антон", "last_name": "Чехов"}),
            author.get_absolute_url(),
        )
        url = reverse("author_delete", args=[author.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertTrue(Author.objects.filter(pk=author.pk).exists())
        self.assertRedirects(self.client.post(url), reverse("authors"))
        self.assertFalse(Author.objects.filter(pk=author.pk).exists())

    def test_book_forms_allow_librarian_to_add_edit_and_delete(self):
        from .models import Genre

        genre = Genre.objects.create(name="Роман")
        self.client.force_login(self.librarian)
        values = {
            "title": "Новая книга", "author": self.author.pk, "summary": "Описание",
            "isbn": "0000000000010", "genre": [genre.pk],
        }
        response = self.client.post(reverse("book_create"), values)
        book = Book.objects.get(isbn=values["isbn"])
        self.assertRedirects(response, book.get_absolute_url())
        values["title"] = "Новое название"
        self.assertRedirects(self.client.post(reverse("book_update", args=[book.pk]), values), book.get_absolute_url())
        book.refresh_from_db()
        self.assertEqual(book.title, values["title"])
        self.assertRedirects(self.client.post(reverse("book_delete", args=[book.pk])), reverse("books"))

    def test_login_logout_and_reset_email(self):
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)
        self.assertRedirects(
            self.client.post(reverse("login"), {"username": "reader", "password": "reader-test-2026"}),
            reverse("my-borrowed"),
        )
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        self.assertRedirects(self.client.post(reverse("logout")), reverse("index"))
        self.assertRedirects(
            self.client.post(reverse("password_reset"), {"email": "reader@example.test"}),
            reverse("password_reset_done"),
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/accounts/reset/", mail.outbox[0].body)
