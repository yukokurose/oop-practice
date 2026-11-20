from django.contrib import admin

from .models import Author, Book, BookInstance, Genre, Language

admin.site.site_header = "Управление LocalLibrary"


class BookInline(admin.TabularInline):
    model = Book
    fields = ("title", "isbn")
    readonly_fields = fields
    show_change_link = True
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class BookInstanceInline(admin.TabularInline):
    model = BookInstance
    extra = 0
    show_change_link = True


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_name", "date_of_birth", "date_of_death")
    search_fields = ("last_name", "first_name")
    inlines = [BookInline]


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "isbn", "language")
    list_filter = ("genre", "language")
    search_fields = ("title", "isbn", "author__last_name")
    filter_horizontal = ("genre",)
    inlines = [BookInstanceInline]


@admin.register(BookInstance)
class BookInstanceAdmin(admin.ModelAdmin):
    list_display = ("book", "status", "borrower", "due_back", "id")
    list_filter = ("status", "due_back")
    search_fields = ("book__title", "borrower__username")
    readonly_fields = ("id",)
    fieldsets = [
        ("Экземпляр", {"fields": ("id", "book", "imprint")}),
        ("Выдача", {"fields": ("status", "borrower", "due_back")}),
    ]


admin.site.register(Genre)
admin.site.register(Language)
