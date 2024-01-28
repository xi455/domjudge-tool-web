import re

from datetime import datetime, timedelta

from django import forms
from django.core.validators import RegexValidator
from pytz import UnknownTimeZoneError, timezone

from app.domservers.models import DomServerClient
from utils.forms import validate_time_format


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


class DomServerContestCreatForm(forms.Form):
    parsed_end = None
    parsed_datetime = None
    parsed_deactivate_time = None

    parsed_scoreboard_freeze_length = None
    parsed_scoreboard_unfreeze_time = None

    name = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=True,
    )
    short_name = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=True,
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
        required=True,
    )
    end_time = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=True,
    )
    activate_time = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"}),
        required=True,
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
        widget=forms.TextInput(
            attrs={
                "class": "form-check-input",
                "type": "checkbox",
                "checked": "checked",
            }
        ),
        required=False,
    )
    process_balloons = forms.BooleanField(
        widget=forms.TextInput(
            attrs={
                "class": "form-check-input",
                "type": "checkbox",
                "checked": "checked",
            }
        ),
        required=False,
    )
    open_to_all_teams = forms.BooleanField(
        widget=forms.TextInput(
            attrs={
                "class": "form-check-input",
                "type": "checkbox",
                "checked": "checked",
            }
        ),
        required=False,
    )
    contest_visible_on_public_scoreboard = forms.BooleanField(
        widget=forms.TextInput(
            attrs={
                "class": "form-check-input",
                "type": "checkbox",
                "checked": "checked",
            }
        ),
        required=False,
    )
    enabled = forms.BooleanField(
        widget=forms.TextInput(
            attrs={
                "class": "form-check-input",
                "type": "checkbox",
                "checked": "checked",
            }
        ),
        required=False,
    )

    def clean_activate_time(self):
        activate_time = self.cleaned_data.get("activate_time")
        if validate_time_format(time_string=activate_time):
            if hasattr(self, "parsed_datetime"):

                if activate_time[0] != "-":
                    raise forms.ValidationError(
                        ("啟用時間必須小於開始時間"),
                        code="invalid",
                    )

            return activate_time

        raise forms.ValidationError(
            ("%(time)s 格式錯誤 請提供有效的啟用時間格式（例如：-12:00:00）"),
            code="invalid",
            params={"time": activate_time},
        )

    def clean_start_time(self):
        start_time = self.cleaned_data.get("start_time")
        try:
            start_time_list = str(start_time).split(" ")

            date_str = f"{start_time_list[0]} {start_time_list[1]}"
            country_name = start_time_list[2]

            parsed_datetime = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

            country_timezone = timezone(country_name)
            self.parsed_datetime = country_timezone.localize(parsed_datetime)

        except (ValueError, UnknownTimeZoneError):
            raise forms.ValidationError(
                ("%(time)s 格式錯誤 請提供有效的日期和時間格式（例如：2023-01-01 14:06:00 Asia/Taipei）"),
                code="invalid",
                params={"time": start_time},
            )

        return start_time

    def clean_scoreboard_freeze_length(self):
        scoreboard_freeze_length = self.cleaned_data.get("scoreboard_freeze_length")

        if scoreboard_freeze_length == "":
            self.parsed_scoreboard_freeze_length = self.parsed_datetime
            return scoreboard_freeze_length

        if validate_time_format(time_string=scoreboard_freeze_length):

            if scoreboard_freeze_length[0] != "+":
                raise forms.ValidationError(
                    ("凍結時間必須大於開始時間"),
                    code="invalid",
                )

            hours, minutes, seconds = map(int, scoreboard_freeze_length[1:].split(":"))
            self.parsed_scoreboard_freeze_length = timedelta(
                hours=hours, minutes=minutes, seconds=seconds
            )

            if hasattr(self, "parsed_datetime") and hasattr(self, "parsed_end"):
                offset_scoreboard_freeze_length = (
                    self.parsed_datetime + self.parsed_scoreboard_freeze_length
                )
                offset_end_time = self.parsed_datetime + self.parsed_end

                if not (
                    self.parsed_datetime
                    <= offset_scoreboard_freeze_length
                    <= offset_end_time
                ):
                    raise forms.ValidationError(
                        ("凍結時間時間點必須在開始時間和結束時間之間"),
                        code="invalid",
                    )

            return scoreboard_freeze_length

        raise forms.ValidationError(
            ("%(time)s 格式錯誤 請提供有效的凍結時間格式（例如：+2:00:00）"),
            code="invalid",
            params={"time": scoreboard_freeze_length},
        )

    def clean_end_time(self):
        end_time = self.cleaned_data.get("end_time")

        if validate_time_format(time_string=end_time):
            if hasattr(self, "parsed_datetime"):
                if end_time[0] != "+":
                    raise forms.ValidationError(
                        ("結束時間必須大於等於開始時間"),
                        code="invalid",
                    )

                hours, minutes, seconds = map(int, end_time[1:].split(":"))
                self.parsed_end = timedelta(
                    hours=hours, minutes=minutes, seconds=seconds
                )

            return end_time

        raise forms.ValidationError(
            ("%(time)s 格式錯誤 請提供有效的結束時間格式（例如：+03:00:00）"),
            code="invalid",
            params={"time": end_time},
        )

    def clean_scoreboard_unfreeze_time(self):
        scoreboard_unfreeze_time = self.cleaned_data.get("scoreboard_unfreeze_time")

        if scoreboard_unfreeze_time == "":
            self.parsed_scoreboard_unfreeze_time = self.parsed_end
            return scoreboard_unfreeze_time

        if validate_time_format(time_string=scoreboard_unfreeze_time):
            if hasattr(self, "parsed_end"):
                if scoreboard_unfreeze_time[0] == "+":
                    hours, minutes, seconds = map(
                        int, scoreboard_unfreeze_time[1:].split(":")
                    )
                    self.parsed_scoreboard_unfreeze_time = timedelta(
                        hours=hours, minutes=minutes, seconds=seconds
                    )

                    if self.parsed_scoreboard_unfreeze_time > self.parsed_end:
                        return scoreboard_unfreeze_time

                raise forms.ValidationError(
                    ("解凍時間必須大於等於結束時間"),
                    code="invalid",
                )

            raise forms.ValidationError(
                ("結束時間欄位疑似有誤請再次檢查"),
                code="invalid",
            )

        raise forms.ValidationError(
            ("%(time)s 格式錯誤 請提供有效的記分牌解凍時間格式（例如：+01:30:00）"),
            code="invalid",
            params={"time": scoreboard_unfreeze_time},
        )

    def clean_deactivate_time(self):
        deactivate_time = self.cleaned_data.get("deactivate_time")

        if deactivate_time == "":
            self.parsed_deactivate_time = self.parsed_scoreboard_unfreeze_time
            return deactivate_time

        if validate_time_format(time_string=deactivate_time):
            if hasattr(self, "parsed_scoreboard_unfreeze_time"):
                if deactivate_time[0] == "+":
                    hours, minutes, seconds = map(int, deactivate_time[1:].split(":"))
                    self.parsed_deactivate_time = timedelta(
                        hours=hours, minutes=minutes, seconds=seconds
                    )

                    if (
                        self.parsed_deactivate_time
                        > self.parsed_scoreboard_unfreeze_time
                    ):
                        return deactivate_time

                raise forms.ValidationError(
                    ("停用時間必須大於等於解凍時間"),
                    code="invalid",
                )

            raise forms.ValidationError(
                ("解凍時間欄位疑似有誤請再次檢查"),
                code="invalid",
            )

        raise forms.ValidationError(
            ("%(time)s 格式錯誤 請提供有效的停用時間格式（例如：+36:00:00）"),
            code="invalid",
            params={"time": deactivate_time},
        )

    # def clean_duration(self):
    #     duration = self.cleaned_data.get("duration")

    #     if validate_time_format(time_string=duration):
    #         return duration
    #     else:
    #         raise forms.ValidationError(("%(time)s 格式錯誤 請提供有效的持續時間格式（例如：+2:00:00）"), code="invalid", params={"time": duration})

    # def clean_penalty_time(self):
    #     penalty_time = self.cleaned_data.get('penalty_time')

    #     if penalty_time is None:
    #         raise forms.ValidationError("懲罰時間不能為空")

    #     if not isinstance(penalty_time, int):
    #         raise forms.ValidationError(("%(time)s 格式錯誤 請提供整數格式的懲罰時間"), params={"time": penalty_time})

    #     return penalty_time
