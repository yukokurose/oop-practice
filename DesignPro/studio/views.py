from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import RegistrationForm
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
    return render(request, "studio/dashboard.html", {
        "requests": request.user.design_requests.select_related("category"),
    })
