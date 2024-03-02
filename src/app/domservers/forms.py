import re

from datetime import datetime, timedelta

from django import forms
from django.core.validators import RegexValidator
from pytz import UnknownTimeZoneError, timezone

from app.domservers.models import DomServerClient, DomServerContest
from utils.forms import validate_country_format


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


class DomServerContestForm(forms.ModelForm):
    parsed_start = None
    parsed_end = None

    parsed_activate_time = None
    parsed_deactivate_time = None

    parsed_scoreboard_freeze_length = None
    parsed_scoreboard_unfreeze_time = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 在這裡設置 boolean_field 的初始值
        self.fields["start_time_enabled"].initial = False
        self.fields["process_balloons"].initial = False
        self.fields["open_to_all_teams"].initial = False
        self.fields["contest_visible_on_public_scoreboard"].initial = False
        self.fields["enabled"].initial = False

    name = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    short_name = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        validators=[
            RegexValidator(
                regex="^[a-zA-Z0-9_-]+$",
                message="只允許使用字母、數字、_和-。",
                code="invalid_short_name",
            )
        ],
    )
    start_time = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    end_time = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    activate_time = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    scoreboard_freeze_length = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=False,
    )
    scoreboard_unfreeze_time = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=False,
    )
    deactivate_time = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=False,
    )
    start_time_enabled = forms.BooleanField(
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "type": "checkbox",
            }
        ),
        required=False,
    )
    process_balloons = forms.BooleanField(
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "type": "checkbox",
            }
        ),
        required=False,
    )
    open_to_all_teams = forms.BooleanField(
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "type": "checkbox",
            }
        ),
        required=False,
    )
    contest_visible_on_public_scoreboard = forms.BooleanField(
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "type": "checkbox",
            }
        ),
        required=False,
    )
    enabled = forms.BooleanField(
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
                "type": "checkbox",
            }
        ),
        required=False,
    )

    def clean_start_time(self):
        start_time = self.cleaned_data.get("start_time")
        dt_format_respone_bool, dt = validate_country_format(time_string=start_time)

        if not dt_format_respone_bool:
            raise forms.ValidationError(
                ("%(time)s 格式錯誤 請提供有效的日期和時間格式（例如：2023-01-01 14:06:00 Asia/Taipei）"),
                code="invalid",
                params={"time": start_time},
            )

        self.parsed_start = dt
        return start_time

    def clean_activate_time(self):
        activate_time = self.cleaned_data.get("activate_time")
        dt_format_respone_bool, dt = validate_country_format(time_string=activate_time)

        if not dt_format_respone_bool:
            raise forms.ValidationError(
                ("%(time)s 格式錯誤 請提供有效的啟動時間格式（例如：2024-01-01 12:00:00 Asia/Taipei）"),
                code="invalid",
                params={"time": activate_time},
            )

        self.parsed_activate_time = dt
        if hasattr(self, "parsed_start"):
            if self.parsed_activate_time > self.parsed_start:
                raise forms.ValidationError(
                    ("啟動時間必須小於開始時間"),
                    code="invalid",
                )
            return activate_time

        raise forms.ValidationError(
            ("開始時間欄位疑似有誤請再次檢查"),
            code="invalid",
        )

    def clean_scoreboard_freeze_length(self):
        scoreboard_freeze_length = self.cleaned_data.get("scoreboard_freeze_length")

        if not scoreboard_freeze_length:
            self.parsed_scoreboard_freeze_length = self.parsed_start
            return scoreboard_freeze_length

        dt_format_respone_bool, dt = validate_country_format(
            time_string=scoreboard_freeze_length
        )

        if not dt_format_respone_bool:
            raise forms.ValidationError(
                ("%(time)s 格式錯誤 請提供有效的凍結時間格式（例如：2024-01-01 15:00:00 Asia/Taipei）"),
                code="invalid",
                params={"time": scoreboard_freeze_length},
            )

        self.parsed_scoreboard_freeze_length = dt
        if self.parsed_start > self.parsed_scoreboard_freeze_length:
            raise forms.ValidationError(
                ("凍結時間必須大於開始時間"),
                code="invalid",
            )

        if hasattr(self, "parsed_start") and hasattr(self, "parsed_end"):
            if not (
                self.parsed_start
                <= self.parsed_scoreboard_freeze_length
                <= self.parsed_end
            ):
                raise forms.ValidationError(
                    ("凍結時間時間點必須在開始時間和結束時間之間"),
                    code="invalid",
                )

            return scoreboard_freeze_length

        raise forms.ValidationError(
            ("開始時間欄位與記分牌結束時間欄位疑似有誤請再次檢查"),
            code="invalid",
        )

    def clean_end_time(self):
        end_time = self.cleaned_data.get("end_time")
        dt_format_respone_bool, dt = validate_country_format(time_string=end_time)

        if not dt_format_respone_bool:
            raise forms.ValidationError(
                ("%(time)s 格式錯誤 請提供有效的記分牌結束時間格式（例如：2024-01-01 18:00:00 Asia/Taipei）"),
                code="invalid",
                params={"time": end_time},
            )

        self.parsed_end = dt
        if hasattr(self, "parsed_start"):
            if self.parsed_start > self.parsed_end:
                raise forms.ValidationError(
                    ("結束時間必須大於等於開始時間"),
                    code="invalid",
                )
            return end_time

        raise forms.ValidationError(
            ("開始時間欄位疑似有誤請再次檢查"),
            code="invalid",
        )

    def clean_scoreboard_unfreeze_time(self):
        scoreboard_unfreeze_time = self.cleaned_data.get("scoreboard_unfreeze_time")

        if not scoreboard_unfreeze_time:
            self.parsed_scoreboard_unfreeze_time = self.parsed_end
            return scoreboard_unfreeze_time

        dt_format_respone_bool, dt = validate_country_format(
            time_string=scoreboard_unfreeze_time
        )

        if not dt_format_respone_bool:
            raise forms.ValidationError(
                ("%(time)s 格式錯誤 請提供有效的記分牌解凍時間格式（例如：2024-01-01 20:00:00 Asia/Taipei）"),
                code="invalid",
                params={"time": scoreboard_unfreeze_time},
            )

        self.parsed_scoreboard_unfreeze_time = dt
        if hasattr(self, "parsed_end"):
            if self.parsed_end > self.parsed_scoreboard_unfreeze_time:
                raise forms.ValidationError(
                    ("解凍時間必須大於等於結束時間"),
                    code="invalid",
                )

            return scoreboard_unfreeze_time

        raise forms.ValidationError(
            ("結束時間欄位疑似有誤請再次檢查"),
            code="invalid",
        )

    def clean_deactivate_time(self):
        deactivate_time = self.cleaned_data.get("deactivate_time")

        if not deactivate_time:
            self.parsed_deactivate_time = self.parsed_scoreboard_unfreeze_time
            return deactivate_time

        dt_format_respone_bool, dt = validate_country_format(
            time_string=deactivate_time
        )

        if not dt_format_respone_bool:
            raise forms.ValidationError(
                ("%(time)s 格式錯誤 請提供有效的停用時間格式（例如：2024-01-01 22:00:00 Asia/Taipei）"),
                code="invalid",
                params={"time": deactivate_time},
            )

        self.parsed_deactivate_time = dt
        if hasattr(self, "parsed_scoreboard_unfreeze_time"):
            if self.parsed_scoreboard_unfreeze_time > self.parsed_deactivate_time:
                raise forms.ValidationError(
                    ("停用時間必須大於等於解凍時間"),
                    code="invalid",
                )
            return deactivate_time

        raise forms.ValidationError(
            ("記分牌解凍時間欄位疑似有誤請再次檢查"),
            code="invalid",
        )

    class Meta:
        model = DomServerContest

        exclude = (
            "owner",
            "server_client",
            "cid",
        )
