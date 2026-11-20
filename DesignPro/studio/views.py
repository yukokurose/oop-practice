from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import DesignRequestForm, RegistrationForm
from .models import DesignRequest


def home(request):
    requests = DesignRequest.objects.all()
    return render(request, "studio/home.html", {
        "completed": requests.filter(status=DesignRequest.Status.COMPLETED).select_related("category")[:4],
        "accepted_count": requests.filter(status=DesignRequest.Status.ACCEPTED).count(),
    })


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = RegistrationForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Регистрация завершена. Войди в личный кабинет.")
        return redirect("login")
    return render(request, "studio/register.html", {"form": form})


class SignInView(LoginView):
    template_name = "studio/login.html"
    redirect_authenticated_user = True

    def get_default_redirect_url(self):
        if self.request.user.is_staff:
            return reverse("admin:index")
        return super().get_default_redirect_url()


@login_required
def dashboard(request):
    requests = request.user.design_requests.select_related("category")
    status = request.GET.get("status", "")
    if status in DesignRequest.Status.values:
        requests = requests.filter(status=status)
    else:
        status = ""
    return render(request, "studio/dashboard.html", {
        "requests": requests,
        "status": status,
        "statuses": DesignRequest.Status.choices,
        "new_status": DesignRequest.Status.NEW,
    })


@login_required
@require_http_methods(["GET", "POST"])
def create_request(request):
    form = DesignRequestForm(
        request.POST if request.method == "POST" else None,
        request.FILES if request.method == "POST" else None,
    )
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.owner = request.user
        item.save()
        messages.success(request, "Заявка создана.")
        return redirect("dashboard")
    return render(request, "studio/request_form.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def delete_request(request, pk):
    own_requests = request.user.design_requests.all()
    item = get_object_or_404(own_requests, pk=pk)
    if item.status != DesignRequest.Status.NEW:
        messages.error(request, "Удалить можно только новую заявку.")
        return redirect("dashboard")
    if request.method == "POST":
        deleted, _ = own_requests.filter(pk=pk, status=DesignRequest.Status.NEW).delete()
        if deleted:
            messages.success(request, "Заявка удалена.")
        else:
            messages.error(request, "Заявка уже удалена или её статус изменился.")
        return redirect("dashboard")
    return render(request, "studio/request_confirm_delete.html", {"item": item})
