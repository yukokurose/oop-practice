from datetime import timedelta

from django import forms
from django.utils import timezone


class RenewBookForm(forms.Form):
    renewal_date = forms.DateField(
        label="Новый срок возврата",
        widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
        input_formats=["%Y-%m-%d"],
        help_text="Выберите дату от сегодняшнего дня до четырёх недель вперёд.",
    )

    def clean_renewal_date(self):
        date = self.cleaned_data["renewal_date"]
        today = timezone.localdate()
        if not today <= date <= today + timedelta(weeks=4):
            raise forms.ValidationError("Дата должна быть в пределах ближайших четырёх недель.")
        return date
