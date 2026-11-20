from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Создаёт локальную учебную учётную запись администратора из ТЗ."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Учебный администратор доступен только в локальном режиме.")
        users = get_user_model().objects
        if users.filter(username__iexact="admin").exists():
            raise CommandError("Учётная запись с логином admin уже существует.")
        users.create_superuser(username="admin", password="admin")
        self.stdout.write(self.style.SUCCESS("Учебная учётная запись создана."))
