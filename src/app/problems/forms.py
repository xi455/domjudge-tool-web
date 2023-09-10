from django import forms

from app.domservers.models import DomServerClient

from .models import ProblemInOut


class ProblemInOutAdminForm(forms.ModelForm):
    class Meta:
        model = ProblemInOut
        fields = "__all__"


class ServerClientForm(forms.ModelForm):
    class Meta:
        model = DomServerClient
        fields = ["name"]
