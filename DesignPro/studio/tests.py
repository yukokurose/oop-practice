from django.test import TestCase
from django.urls import reverse

from .models import Category, DesignRequest, User


class GuestTests(TestCase):
    password = "W9p!qR48JK"

    def registration_data(self, **changes):
        return {
            "full_name": "Анна Иванова-Петрова",
            "username": "anna-design",
            "email": "anna@example.com",
            "password1": self.password,
            "password2": self.password,
            "consent": "on",
            **changes,
        }

    def test_guest_can_open_home_but_not_dashboard(self):
        self.assertContains(self.client.get(reverse("home")), "Готовых проектов пока нет.")
        self.assertRedirects(self.client.get(reverse("dashboard")), "/login/?next=/account/")

    def test_guest_can_register_and_sign_in(self):
        response = self.client.post(reverse("register"), self.registration_data())
        self.assertRedirects(response, reverse("login"))
        user = User.objects.get(username="anna-design")
        self.assertTrue(user.check_password(self.password))
        self.assertIsNotNone(user.consented_at)
        self.assertFalse(user.is_staff)

        response = self.client.post(reverse("login"), {
            "username": user.username,
            "password": self.password,
        }, follow=True)
        self.assertRedirects(response, reverse("dashboard"))
        self.assertContains(response, user.full_name)

    def test_registration_rejects_invalid_fields(self):
        for field, value in {
            "full_name": "Anna",
            "username": "анна",
            "email": "not-an-email",
            "password1": "12345678",
            "password2": "another-password",
            "consent": "",
        }.items():
            with self.subTest(field=field):
                data = self.registration_data(**{field: value})
                if field == "password1":
                    data["password2"] = value
                response = self.client.post(reverse("register"), data)
                error_field = "password2" if field == "password1" else field
                self.assertIn(error_field, response.context["form"].errors)
                self.assertContains(response, 'class="field invalid')
        self.assertEqual(User.objects.count(), 0)

    def test_registration_rejects_duplicate_login(self):
        User.objects.create_user(username="Anna-Design")
        response = self.client.post(reverse("register"), self.registration_data())
        self.assertIn("username", response.context["form"].errors)
        self.assertEqual(User.objects.count(), 1)

    def test_wrong_password_leaves_guest_signed_out(self):
        user = User.objects.create_user(username="anna", password=self.password)
        response = self.client.post(reverse("login"), {
            "username": user.username,
            "password": "incorrect",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_admin_is_sent_to_admin_panel(self):
        admin = User.objects.create_superuser(username="admin", password=self.password)
        response = self.client.post(reverse("login"), {
            "username": admin.username,
            "password": self.password,
        })
        self.assertRedirects(response, reverse("admin:index"))

    def test_home_shows_latest_four_completed_projects_and_accepted_count(self):
        user = User.objects.create_user(username="anna")
        category = Category.objects.create(name="Кухня")
        for number in range(6):
            DesignRequest.objects.create(
                owner=user, title=f"Проект {number}", category=category,
                status=DesignRequest.Status.COMPLETED, design=f"designs/{number}.jpg",
            )
        DesignRequest.objects.create(
            owner=user, title="Заявка в работе", category=category,
            status=DesignRequest.Status.ACCEPTED,
        )
        DesignRequest.objects.create(owner=user, title="Новая заявка", category=category)

        response = self.client.get(reverse("home"))
        self.assertEqual(response.context["accepted_count"], 1)
        completed = [item.title for item in response.context["completed"]]
        self.assertEqual(completed, ["Проект 5", "Проект 4", "Проект 3", "Проект 2"])
        self.assertContains(response, "/media/designs/5.jpg")
        self.assertContains(response, category.name)
        self.assertContains(response, "<time ")
        self.assertNotContains(response, "Заявка в работе")

    def test_dashboard_only_displays_current_users_requests(self):
        user = User.objects.create_user(username="anna")
        other = User.objects.create_user(username="other")
        category = Category.objects.create(name="Кухня")
        DesignRequest.objects.create(owner=user, title="Моя заявка", category=category)
        DesignRequest.objects.create(owner=other, title="Чужая заявка", category=category)
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Моя заявка")
        self.assertNotContains(response, "Чужая заявка")
