from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Snippet


class SnippetTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.owner = users.create_user(username="alice")
        cls.other = users.create_user(username="bob")
        cls.snippet = Snippet.objects.create(owner=cls.owner, code="print('hello')")

    def test_anonymous_can_read_root_snippets_and_users(self):
        response = self.client.get(reverse("api-root"), format="json")
        self.assertEqual(response.status_code, 200)
        for name, route in (("snippets", "snippet-list"), ("users", "user-list")):
            self.assertEqual(response.data[name], "http://testserver" + reverse(route))
        response = self.client.get(reverse("snippet-detail", args=[self.snippet.pk]))
        self.assertEqual(response.data["owner"], self.owner.username)
        self.assertTrue(response.data["highlight"].startswith(
            "http://testserver" + reverse("snippet-highlight", args=[self.snippet.pk]).rstrip("/")
        ))
        response = self.client.get(reverse("user-detail", args=[self.owner.pk]))
        self.assertEqual(response.data["snippets"], [
            "http://testserver" + reverse("snippet-detail", args=[self.snippet.pk]),
        ])

    def test_anonymous_cannot_create(self):
        response = self.client.post(reverse("snippet-list"), {"code": "pass"}, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Snippet.objects.count(), 1)

    def test_authenticated_creation_sets_owner_and_validates_choices(self):
        self.client.force_authenticate(self.owner)
        url = reverse("snippet-list")
        code = "if True:\n    print('hello')\n"
        response = self.client.post(url, {"code": code, "owner": self.other.username}, format="json")
        self.assertEqual(response.status_code, 201)
        item = Snippet.objects.get(pk=response.data["id"])
        self.assertEqual(item.owner, self.owner)
        self.assertEqual(item.code, code)
        self.assertEqual(item.language, "python")
        self.assertEqual(item.style, "friendly")
        response = self.client.post(url, {"code": code, "language": "invalid", "style": "invalid"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("language", response.data)
        self.assertIn("style", response.data)

    def test_edit_and_delete_are_limited_to_owner(self):
        url = reverse("snippet-detail", args=[self.snippet.pk])
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.patch(url, {"code": "pass"}, format="json").status_code, 403)
        self.assertEqual(self.client.delete(url).status_code, 403)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.patch(url, {"code": "print(42)"}, format="json").status_code, 200)
        self.snippet.refresh_from_db()
        self.assertEqual(self.snippet.code, "print(42)")
        self.assertIn("42", self.snippet.highlighted)
        self.assertEqual(self.client.delete(url).status_code, 204)

    def test_highlight_escapes_code_and_supports_line_numbers(self):
        item = Snippet.objects.create(
            owner=self.owner, language="html", code="<script>alert(1)</script>", linenos=True,
        )
        response = self.client.get(reverse("snippet-highlight", args=[item.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/html"))
        self.assertContains(response, "linenodiv")
        self.assertNotContains(response, "<script>")
