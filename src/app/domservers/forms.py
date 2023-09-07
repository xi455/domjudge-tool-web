from django import forms

from app.domservers.models import DomServerClient


class DomServerAccountForm(forms.ModelForm):
    password_field = forms.CharField(
        required=False,
        label="密碼",
        widget=forms.PasswordInput(attrs={"class": "vTextField"}),
        help_text="更新密碼",
    )

    class Meta:
        model = DomServerClient
        fields = (
            "name",
            "host",
            "username",
            "password_field",
            "disable_ssl",
            "timeout",
            "category_id",
            "affiliation_id",
            "affiliation_country",
            "owner",
            "version",
            "api_version",
        )
