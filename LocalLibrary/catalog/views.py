from datetime import timedelta

from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import generic

from .forms import RenewBookForm
from .models import Author, Book, BookInstance, Genre


def index(request):
    visits = request.session.get("num_visits", 0) + 1
    request.session["num_visits"] = visits
    return render(request, "catalog/index.html", {
        "num_books": Book.objects.count(),
        "num_instances": BookInstance.objects.count(),
        "num_available": BookInstance.objects.filter(status=BookInstance.Status.AVAILABLE).count(),
        "num_authors": Author.objects.count(),
        "num_genres": Genre.objects.count(),
        "num_visits": visits,
    })


class BookListView(generic.ListView):
    queryset = Book.objects.select_related("author", "language")
    paginate_by = 6


class BookDetailView(generic.DetailView):
    queryset = Book.objects.select_related("author", "language").prefetch_related("genre", "copies")


class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 6


class AuthorDetailView(generic.DetailView):
    queryset = Author.objects.prefetch_related("book_set")


class LoanListView(generic.ListView):
    template_name = "catalog/loans.html"
    context_object_name = "loans"
    paginate_by = 10
    queryset = BookInstance.objects.filter(status=BookInstance.Status.ON_LOAN).select_related("book", "borrower")


class MyBorrowedView(LoginRequiredMixin, LoanListView):
    extra_context = {"page_title": "Мои выдачи"}

    def get_queryset(self):
        return super().get_queryset().filter(borrower=self.request.user)


class AllBorrowedView(PermissionRequiredMixin, LoanListView):
    permission_required = "catalog.can_mark_returned"
    extra_context = {"page_title": "Все выдачи"}


@permission_required("catalog.can_mark_returned", raise_exception=True)
def renew_book(request, pk):
    copy = get_object_or_404(
        BookInstance.objects.select_related("book", "borrower"),
        pk=pk, status=BookInstance.Status.ON_LOAN,
    )
    form = RenewBookForm(
        request.POST if request.method == "POST" else None,
        initial={"renewal_date": timezone.localdate() + timedelta(weeks=3)},
    )
    if request.method == "POST" and form.is_valid():
        copy.due_back = form.cleaned_data["renewal_date"]
        copy.save(update_fields=["due_back"])
        return redirect("all-borrowed")
    return render(request, "catalog/renew.html", {"form": form, "copy": copy})


class AuthorCreate(PermissionRequiredMixin, generic.CreateView):
    model = Author
    permission_required = "catalog.add_author"
    fields = ["first_name", "last_name", "date_of_birth", "date_of_death"]
    extra_context = {"page_title": "Добавить автора"}


class AuthorUpdate(PermissionRequiredMixin, generic.UpdateView):
    model = Author
    permission_required = "catalog.change_author"
    fields = AuthorCreate.fields
    extra_context = {"page_title": "Редактировать автора"}


class AuthorDelete(PermissionRequiredMixin, generic.DeleteView):
    model = Author
    permission_required = "catalog.delete_author"
    success_url = reverse_lazy("authors")
    extra_context = {"page_title": "Удалить автора"}


class BookCreate(PermissionRequiredMixin, generic.CreateView):
    model = Book
    permission_required = "catalog.add_book"
    fields = ["title", "author", "summary", "isbn", "genre", "language"]
    template_name = "catalog/book_form.html"
    extra_context = {"page_title": "Добавить книгу"}


class BookUpdate(PermissionRequiredMixin, generic.UpdateView):
    model = Book
    permission_required = "catalog.change_book"
    fields = BookCreate.fields
    template_name = "catalog/book_form.html"
    extra_context = {"page_title": "Редактировать книгу"}


class BookDelete(PermissionRequiredMixin, generic.DeleteView):
    model = Book
    permission_required = "catalog.delete_book"
    success_url = reverse_lazy("books")
    extra_context = {"page_title": "Удалить книгу"}
