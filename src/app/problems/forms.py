from django import forms

from app.domservers.models import DomServerClient
from app.problems.models import Problem

from .models import ProblemInOut


class ProblemInOutAdminForm(forms.ModelForm):
    class Meta:
        model = ProblemInOut
        fields = "__all__"


class ServerClientForm(forms.ModelForm):
    class Meta:
        model = DomServerClient
        fields = ["name"]


class ProblemNameForm(forms.ModelForm):
    class Meta:
        model = Problem
        fields = ["name"]

    def clean_name(self):
        name_value = self.cleaned_data.get("name")

        if name_value[0].isdigit():
            raise forms.ValidationError("題目名稱首字不可為數字")
        return name_value
