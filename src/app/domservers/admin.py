from django.contrib import admin
from django.shortcuts import render
from django_object_actions import DjangoObjectActions, action

from app.domservers.forms import DomServerAccountForm
from app.domservers.models import DomServerClient, ContestRecord
from utils.admins import create_problem_crawler, get_contest_all_and_page_obj
from django_object_actions import DjangoObjectActions

# Register your models here.

@admin.register(ContestRecord)
class ContestRecordAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = [field.name for field in ContestRecord._meta.get_fields()]



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
        getdata = request.GET
        page_obj = get_contest_all_and_page_obj(getdata, problem_crawler)
        
        context = {
            "page_obj": page_obj,  # 將 page_obj 加入到上下文中
            "server_client_name": obj.name,
            "server_client_id": obj.id,

            "opts": obj._meta,  # 獲取模型的應用標籤
            "available_apps": self.admin_site.each_context(request).get("available_apps"),  # 獲取 sidebar 所有應用
        }


        return render(request, "contest_list.html", context)
