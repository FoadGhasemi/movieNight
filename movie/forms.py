from django import forms
from .models import UserMovieEntry

class EntryForm(forms.ModelForm):
    class Meta:
        model = UserMovieEntry
        fields = ["status", "rating", "review", "date_watched"]

        widgets = {
            "status": forms.Select(attrs={"class": "form-control"}),
            "rating": forms.NumberInput(attrs={"class": "form-control"}),
            "review": forms.Textarea(attrs={"class": "form-control"}),
            "date_watched": forms.DateInput(attrs={"class": "rounded-2"}),
        }