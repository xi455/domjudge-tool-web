from typing import Any

from django.urls import path
from django.contrib import admin
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.shortcuts import render
from django_object_actions import DjangoObjectActions, action

from app.domservers.forms import DomServerAccountForm
from app.domservers.models import DomServerClient, DomServerContest
from utils.admins import create_problem_crawler, get_contest_all_and_page_obj
from utils.views import get_available_apps

# Register your models here.


@admin.register(DomServerContest)
class DomServerContestAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = [
        "owner",
        "server_client",
        "short_name",
        "cid",
    ]


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

    change_actions = ("get_contest_info_view",)

    form = DomServerAccountForm

    def save_form(self, request, form, change):
        password_field = form.cleaned_data["password_field"]

        if password_field:
            form.instance.mask_password = password_field

        return super().save_form(request, form, change)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        queryset = super().get_queryset(request)

        if request.user.is_superuser:
            return queryset

        return queryset.filter(owner=request.user)
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("contest-items/<obj_id>/", self.admin_site.admin_view(self.get_contest_info_view), name="contest-items"),
        ]
        return custom_urls + urls

    @action(label="取得考區資訊")
    def get_contest_info_view(self, request, obj=None, obj_id=None):
        if obj_id is not None:
            obj = DomServerClient.objects.get(id=obj_id)


        if "page_number" in request.session:
            page_number = request.session["page_number"]

            new_get = request.GET.copy()
            new_get["page"] = page_number

            request.GET = new_get

            del request.session["page_number"]

        page_obj = get_contest_all_and_page_obj(request, obj)

        context = {
            "page_obj": page_obj,  # 將 page_obj 加入到上下文中
            "server_client_name": obj.name,
            "server_client_id": obj.id,
            "opts": obj._meta,  # 獲取模型的應用標籤
            "available_apps": get_available_apps(request),  # 獲取 sidebar 所有應用
        }

        # obj = DomServerClient.objects.all().first()
        # problem_crawler = create_problem_crawler(obj)
        # problem_crawler.get_contest_problems_detail_info("2")

        return render(request, "contest_list.html", context)