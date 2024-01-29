from django.contrib import admin
from django.shortcuts import render
from django_object_actions import DjangoObjectActions, action

from app.domservers.forms import DomServerAccountForm
from app.domservers.models import DomServerClient
from utils.admins import create_problem_crawler

# Register your models here.


@admin.register(DomServerClient)
class DomServerAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = [
        "name",
        "host",
        "username",
        "disable_ssl",
        "timeout",
        "category_id",
        "affiliation_id",
        "affiliation_country",
        "owner",
        "version",
        "api_version",
    ]

    change_actions = ("get_contest_info",)

    form = DomServerAccountForm

    def save_form(self, request, form, change):
        password_field = form.cleaned_data["password_field"]

        if password_field:
            form.instance.mask_password = password_field

        return super().save_form(request, form, change)

    @action(label="取得考區資訊")
    def get_contest_info(self, request, obj):
        problem_crawler = create_problem_crawler(obj)
        contest_dicts = problem_crawler.get_contest_all()

        context = {
            "contest_dicts": contest_dicts,
            "server_client_name": obj.name,
            "server_client_id": obj.id,
        }

        return render(request, "contest_list.html", context)
