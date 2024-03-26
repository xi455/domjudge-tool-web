from typing import Any

from django.urls import path
from django.contrib import admin, messages
from django.db import transaction
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.shortcuts import render
from django_object_actions import DjangoObjectActions, action

from app.domservers.forms import DomServerAccountForm
from app.domservers.models import DomServerClient, DomServerUser, DomServerContest
from app.domservers.views.validator import validator_demo_contest_exist

from app.problems import exceptions as problems_exceptions

from app.users.models import User

from utils.admins import create_problem_crawler, get_contest_all_and_page_obj
from utils.views import get_available_apps
from utils.validator_pydantic import DomServerClientModel


# Register your models here.



@admin.register(DomServerContest)
class DomServerContestAdmin(admin.ModelAdmin):
    list_display = [
        "owner",
        "server_client",
        "short_name",
        "cid",
    ]

    def has_module_permission(self, request):
        return request.user.is_superuser
    

@admin.register(DomServerUser)
class DomServerUserAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = [
        "owner",
        "username",
        "server_client",
    ]
    form = DomServerAccountForm

    change_actions = ("get_contest_info_view",)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        if request.user.is_superuser:
            return queryset

        return queryset.filter(owner=request.user)

    def save_form(self, request, form, change):
        password_field = form.cleaned_data["password_field"]
        owner = User.objects.get(username=request.user)

        form.instance.mask_password = password_field
        # form.instance.owner = owner 實驗用，需在解除註解

        return super().save_form(request, form, change)
    
    def save_model(self, request, obj, form, change) -> None:
        server_client = DomServerClientModel(
            host=form.instance.server_client.host,
            username=obj.username,
            mask_password=obj.mask_password,
        )

        problem_crawler = create_problem_crawler(server_client)

        try:
            problem_crawler.login()
            result = validator_demo_contest_exist(problem_crawler, obj.server_client)
            if not result:
                raise problems_exceptions.ProblemDownloaderDemoContestNotFoundException("Demo contest not found.")
            
            messages.success(request, "嘗試登入成功")

            super().save_model(request, obj, form, change)
        except problems_exceptions.ProblemDownloaderLoginException as e:
            messages.error(request, "嘗試登入失敗，請檢查帳號密碼是否正確")
            print(e)
        except problems_exceptions.ProblemDownloaderDemoContestNotFoundException as e:
            messages.error(request, "Demo 考場建置失敗，請告知維護人員")
            print(e)


    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("contest-items/<obj_id>/", self.admin_site.admin_view(self.get_contest_info_view), name="contest-items"),
        ]
        return custom_urls + urls

    @action(label="取得考區資訊")
    def get_contest_info_view(self, request, obj=None, obj_id=None):
        if obj_id is not None:
            obj = DomServerUser.objects.get(id=obj_id)

        server_client = DomServerClientModel(
            host=obj.server_client.host,
            username=obj.username,
            mask_password=obj.mask_password,
        )

        problem_crawler = create_problem_crawler(server_client)
        try:
            problem_crawler.login()
            messages.success(request, "登入成功")

        except problems_exceptions.ProblemDownloaderLoginException as e:
            messages.error(request, "登入失敗，請檢查帳號密碼是否正確")
            print(e)

        if "page_number" in request.session:
            page_number = request.session["page_number"]

            new_get = request.GET.copy()
            new_get["page"] = page_number

            request.GET = new_get

            del request.session["page_number"]

        page_obj = get_contest_all_and_page_obj(request, obj.server_client)

        context = {
            "page_obj": page_obj,  # 將 page_obj 加入到上下文中
            "server_client_name": obj.server_client.name,
            "server_user": obj,
            "opts": obj._meta,  # 獲取模型的應用標籤
            "available_apps": get_available_apps(request),  # 獲取 sidebar 所有應用
        }

        return render(request, "contest_list.html", context)


@admin.register(DomServerClient)
class DomServerAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = [
        "name",
        "host",
        "disable_ssl",
        "timeout",
        "version",
        "api_version",
    ]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        queryset = super().get_queryset(request)

        if request.user.is_superuser:
            return queryset

        return queryset.filter(owner=request.user)
    
    def has_module_permission(self, request):
        return request.user.is_superuser