from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Category, DesignRequest, User


class AdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_superuser(username="studio-admin")
        cls.owner = User.objects.create_user(username="owner")
        cls.category = Category.objects.get(name="Эскиз")
        cls.item = DesignRequest.objects.create(
            title="Спальня", owner=cls.owner, category=cls.category, description="План комнаты",
        )

    def setUp(self):
        self.client.force_login(self.staff)
        self.status_url = reverse("admin:studio_designrequest_status", args=[self.item.pk])
        self.detail_url = reverse("admin:studio_designrequest_change", args=[self.item.pk])

    def test_admin_can_reach_status_form_from_request_details(self):
        listing = self.client.get(reverse("admin:studio_designrequest_changelist"))
        self.assertContains(listing, self.detail_url)
        detail = self.client.get(self.detail_url)
        self.assertContains(detail, self.status_url)
        delete_url = reverse("admin:studio_designrequest_delete", args=[self.item.pk])
        self.assertNotContains(detail, delete_url)
        self.assertEqual(self.client.post(delete_url, {"post": "yes"}).status_code, 403)
        self.assertContains(self.client.get(self.status_url), "Сохранить статус")

    def test_accept_requires_comment_and_locks_further_changes(self):
        status = DesignRequest.Status.ACCEPTED
        response = self.client.post(self.status_url, {"status": status, "comment": "  "})
        self.assertFormError(response.context["form"], "comment", "Напишите комментарий для принятия заявки в работу.")
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, DesignRequest.Status.NEW)

        response = self.client.post(self.status_url, {"status": status, "comment": "Начинаем с замеров."})
        self.assertRedirects(response, self.detail_url)
        self.assertNotContains(self.client.get(self.detail_url), self.status_url)
        self.client.post(self.status_url, {"status": status, "comment": "Позднее изменение"})
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, status)
        self.assertEqual(self.item.comment, "Начинаем с замеров.")
        self.assertEqual(self.client.get(reverse("home")).context["accepted_count"], 1)

    def test_completion_requires_image_and_publishes_design_on_home(self):
        status = DesignRequest.Status.COMPLETED
        response = self.client.post(self.status_url, {"status": status})
        self.assertFormError(response.context["form"], "design", "Прикрепите изображение готового дизайна.")
        response = self.client.post(self.status_url, {
            "status": status, "design": SimpleUploadedFile("bad.png", b"invalid"),
        })
        self.assertIn("design", response.context["form"].errors)
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, DesignRequest.Status.NEW)

        buffer = BytesIO()
        Image.new("RGB", (4, 4)).save(buffer, format="PNG")
        with TemporaryDirectory() as media_root, self.settings(MEDIA_ROOT=media_root):
            response = self.client.post(self.status_url, {
                "status": status, "design": SimpleUploadedFile("design.png", buffer.getvalue()),
            })
            self.assertRedirects(response, self.detail_url)
            self.client.post(self.status_url, {
                "status": DesignRequest.Status.ACCEPTED, "comment": "Повторная обработка",
            })
            self.item.refresh_from_db()
            self.assertEqual(self.item.status, status)
            self.assertTrue(Path(self.item.design.path).is_file())
            self.assertContains(self.client.get(reverse("home")), self.item.design.url)

    def test_only_authorized_admin_can_change_status_and_cannot_use_details_form(self):
        payload = {"status": DesignRequest.Status.ACCEPTED, "comment": "Обработка"}
        self.assertEqual(self.client.post(self.detail_url, payload).status_code, 403)
        self.client.force_login(User.objects.create_user(username="staff", is_staff=True))
        self.assertEqual(self.client.post(self.status_url, payload).status_code, 403)
        self.client.force_login(self.owner)
        self.assertRedirects(self.client.post(self.status_url, payload), f"/superadmin/login/?next={self.status_url}")
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, DesignRequest.Status.NEW)

    def test_admin_can_add_and_delete_category_with_its_requests(self):
        listing = reverse("admin:studio_category_changelist")
        response = self.client.post(reverse("admin:studio_category_add"), {"name": "Планировка", "_save": "1"})
        self.assertRedirects(response, listing)
        category = Category.objects.get(name="Планировка")
        url = reverse("admin:studio_category_delete", args=[self.category.pk])
        self.assertContains(self.client.get(url), self.item.title)
        self.assertRedirects(self.client.post(url, {"post": "yes"}), listing)
        self.assertFalse(Category.objects.filter(pk=self.category.pk).exists())
        self.assertFalse(DesignRequest.objects.filter(pk=self.item.pk).exists())
        self.assertTrue(Category.objects.filter(pk=category.pk).exists())
