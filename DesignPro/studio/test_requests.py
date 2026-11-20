from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Category, DesignRequest, User


class RequestTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="anna")
        cls.other = User.objects.create_user(username="other")
        cls.category = Category.objects.get(name="Эскиз")

    def setUp(self):
        self.client.force_login(self.user)

    def photo(self, name="room.png", image_format="PNG", padding=b""):
        buffer = BytesIO()
        Image.new("RGB", (4, 4)).save(buffer, format=image_format)
        return SimpleUploadedFile(name, buffer.getvalue() + padding)

    def create_data(self, **changes):
        return {
            "title": "Гостиная",
            "description": "Светлый интерьер.",
            "category": self.category.pk,
            "photo": self.photo(),
            **changes,
        }

    def request(self, title, *, owner=None, status=DesignRequest.Status.NEW):
        return DesignRequest.objects.create(
            owner=owner or self.user, title=title, description="Описание комнаты",
            category=self.category, status=status,
        )

    def test_logout_requires_post_and_clears_session(self):
        url = reverse("logout")
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertRedirects(self.client.post(url), reverse("home"))
        self.assertRedirects(self.client.get(reverse("dashboard")), "/login/?next=/account/")

    def test_guest_cannot_create_or_delete(self):
        item = self.request("Новая")
        self.client.logout()
        for url in (reverse("request_create"), reverse("request_delete", args=[item.pk])):
            with self.subTest(url=url):
                self.assertRedirects(self.client.post(url), f"/login/?next={url}")
        self.assertTrue(DesignRequest.objects.filter(pk=item.pk).exists())

    def test_create_assigns_owner_status_and_time_and_saves_photo(self):
        with TemporaryDirectory() as media_root, self.settings(MEDIA_ROOT=media_root):
            response = self.client.post(reverse("request_create"), self.create_data(
                owner=self.other.pk, status=DesignRequest.Status.COMPLETED,
            ))
            self.assertRedirects(response, reverse("dashboard"))
            item = DesignRequest.objects.get()
            self.assertEqual(item.owner, self.user)
            self.assertEqual(item.status, DesignRequest.Status.NEW)
            self.assertIsNotNone(item.created_at)
            self.assertTrue(Path(item.photo.path).is_file())

    def test_create_rejects_missing_fields_and_invalid_images(self):
        url = reverse("request_create")
        cases = [
            ("title", ""), ("description", ""), ("category", ""), ("category", -1),
            ("photo", ""), ("photo", SimpleUploadedFile("room.png", b"invalid")),
            ("photo", self.photo(name="room.gif", image_format="GIF")),
            ("photo", self.photo(name="room.jpg")),
            ("photo", self.photo(padding=b"x" * (2 * 1024 * 1024))),
        ]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                response = self.client.post(url, self.create_data(**{field: value}))
                self.assertIn(field, response.context["form"].errors)
        self.assertFalse(DesignRequest.objects.exists())

    def test_dashboard_orders_and_filters_own_requests(self):
        first = self.request("Первая заявка")
        second = self.request("Вторая заявка", status=DesignRequest.Status.ACCEPTED)
        self.request("Чужая заявка", owner=self.other, status=DesignRequest.Status.ACCEPTED)
        url = reverse("dashboard")
        response = self.client.get(url)
        self.assertEqual(list(response.context["requests"]), [second, first])
        for label in (first.description, self.category.name, first.get_status_display(), "<time "):
            self.assertContains(response, label)

        filtered = self.client.get(url, {"status": DesignRequest.Status.ACCEPTED})
        self.assertEqual(list(filtered.context["requests"]), [second])
        self.assertNotContains(filtered, "Удалить заявку")

    def test_own_new_request_needs_confirmation_before_deletion(self):
        item = self.request("Новая")
        url = reverse("request_delete", args=[item.pk])
        self.assertContains(self.client.get(url), "Удалить заявку?")
        self.assertTrue(DesignRequest.objects.filter(pk=item.pk).exists())
        self.assertRedirects(self.client.post(url), reverse("dashboard"))
        self.assertFalse(DesignRequest.objects.filter(pk=item.pk).exists())

    def test_cannot_delete_other_users_request_or_processed_request(self):
        other = self.request("Чужая заявка", owner=self.other)
        self.assertEqual(self.client.post(reverse("request_delete", args=[other.pk])).status_code, 404)
        for status in (DesignRequest.Status.ACCEPTED, DesignRequest.Status.COMPLETED):
            with self.subTest(status=status):
                item = self.request("Обработанная заявка", status=status)
                response = self.client.post(reverse("request_delete", args=[item.pk]), follow=True)
                self.assertContains(response, "Удалить можно только новую заявку.")
        self.assertEqual(DesignRequest.objects.count(), 3)
