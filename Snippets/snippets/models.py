from django.conf import settings
from django.db import models
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name


class Snippet(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=100, blank=True, default="")
    code = models.TextField()
    linenos = models.BooleanField(default=False)
    language = models.CharField(max_length=100, default="python")
    style = models.CharField(max_length=100, default="friendly")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="snippets", on_delete=models.CASCADE)
    highlighted = models.TextField(editable=False)

    class Meta:
        ordering = ("created", "pk")

    def save(self, *args, **kwargs):
        lexer = get_lexer_by_name(self.language)
        formatter = HtmlFormatter(full=True, linenos="table" if self.linenos else False, style=self.style)
        self.highlighted = highlight(self.code, lexer, formatter)
        if kwargs.get("update_fields"):
            kwargs["update_fields"] = {*kwargs["update_fields"], "highlighted"}
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title or f"Сниппет {self.pk}"
