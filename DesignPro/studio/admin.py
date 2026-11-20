from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods

from .forms import RequestStatusForm
from .models import Category, DesignRequest, User


@admin.register(User)
class StudioUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Профиль Design.pro", {"fields": ("full_name", "consented_at")}),)
    readonly_fields = ("consented_at",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(DesignRequest)
class DesignRequestAdmin(admin.ModelAdmin):
    actions = None
    list_display = ("title", "owner", "category", "status", "created_at")
    list_filter = ("status", "category")
    list_select_related = ("owner", "category")
    search_fields = ("title", "owner__username")
    fields = (
        "title", "description", "owner", "category", "photo",
        "created_at", "status", "comment", "design",
    )
    readonly_fields = fields
    change_form_template = "admin/studio/designrequest/change_form.html"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def delete_view(self, request, object_id, extra_context=None):
        # Django still checks the model's delete permission for category cascades.
        raise PermissionDenied

    def get_urls(self):
        return [
            path(
                "<int:pk>/status/",
                self.admin_site.admin_view(self.change_status),
                name="studio_designrequest_status",
            ),
            *super().get_urls(),
        ]

    def change_view(self, request, object_id, form_url="", extra_context=None):
        item = self.get_object(request, object_id)
        context = {**(extra_context or {}), "show_delete": False}
        if item and item.status == DesignRequest.Status.NEW and request.user.has_perm("studio.change_designrequest"):
            context["status_url"] = reverse("admin:studio_designrequest_status", args=[item.pk])
        return super().change_view(request, object_id, form_url, context)

    @method_decorator(require_http_methods(["GET", "POST"]))
    def change_status(self, request, pk):
        if not request.user.has_perm("studio.change_designrequest"):
            raise PermissionDenied
        requests = self.get_queryset(request)
        item = get_object_or_404(requests, pk=pk)
        detail_url = reverse("admin:studio_designrequest_change", args=[item.pk])
        if item.status != DesignRequest.Status.NEW:
            self.message_user(request, "Статус этой заявки уже изменён.", level="warning")
            return redirect(detail_url)

        form = RequestStatusForm(
            request.POST if request.method == "POST" else None,
            request.FILES if request.method == "POST" else None,
        )
        if request.method == "POST" and form.is_valid():
            status = form.cleaned_data["status"]
            comment = form.cleaned_data["comment"] if status == DesignRequest.Status.ACCEPTED else ""
            with transaction.atomic(using=requests.db):
                changed = requests.filter(pk=pk, status=DesignRequest.Status.NEW).update(
                    status=status, comment=comment,
                )
                if changed and status == DesignRequest.Status.COMPLETED:
                    design = form.cleaned_data["design"]
                    item.design.save(design.name, design, save=False)
                    requests.filter(pk=pk).update(design=item.design.name)
            if changed:
                self.message_user(request, "Статус заявки изменён.", level="success")
            else:
                self.message_user(request, "Заявка удалена или её статус уже изменён.", level="warning")
                return redirect("admin:studio_designrequest_changelist")
            return redirect(detail_url)

        return TemplateResponse(request, "admin/studio/designrequest/change_status.html", {
            **self.admin_site.each_context(request),
            "title": "Изменение статуса заявки",
            "item": item,
            "form": form,
            "detail_url": detail_url,
        })


admin.site.site_header = "Администрирование Design.pro"
