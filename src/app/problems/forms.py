from django import forms

from .models import ProblemInOut


class ProblemInOutAdminForm(forms.ModelForm):
    class Meta:
        model = ProblemInOut
        fields = "__all__"
