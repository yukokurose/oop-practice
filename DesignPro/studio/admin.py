from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class StudioUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Профиль Design.pro", {"fields": ("full_name", "consented_at")}),)
    readonly_fields = ("consented_at",)


admin.site.site_header = "Администрирование Design.pro"
