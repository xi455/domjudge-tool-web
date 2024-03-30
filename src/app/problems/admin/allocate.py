from django.contrib import admin, messages
from django.http import HttpRequest
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django_object_actions import DjangoObjectActions, action

from pydantic import BaseModel

from app.domservers.models import DomServerClient, DomServerUser, DomServerContest
from utils.admins import (
    create_problem_crawler,
    get_newest_problems_log,
    upload_problem_info_process,
)
from utils.views import get_available_apps
from utils.validator_pydantic import DomServerClientModel

from app.problems.forms import ProblemNameForm
from app.problems.models import Problem, ProblemInOut, ProblemServerLog
from app.problems.admin import testcase as testcase_admin
from app.problems import exceptions as problem_exceptions


class ProblemInOutInline(admin.TabularInline):
    model = ProblemInOut
    max_num = 10
    extra = 1


@admin.register(ProblemServerLog)
class ProblemServerLogAdmin(DjangoObjectActions, admin.ModelAdmin):
    list_display = (
        "owner",
        "problem",
        "server_client",
        "web_problem_id",
        "contest",
        "web_problem_state",
    )

    def has_module_permission(self, request):
        return request.user.is_superuser


@admin.register(Problem)
class ProblemAdmin(DjangoObjectActions, admin.ModelAdmin):

    # form = ProblemNameForm

    list_display = (
        "name",
        "time_limit",
        "owner",
        "id",
        "make_zip",
        "replacement_problem",
    )
    list_filter = ("create_at", "update_at")
    search_fields = ["name"]
    inlines = [ProblemInOutInline]
    readonly_fields = ("id", "owner", "update_illustrate")
    fieldsets = (
        (
            None,
            {
                "fields": ("id", "owner", "update_illustrate"),
            },
        ),
        (
            "題目資訊",
            {
                "fields": (
                    "name",
                    "description_file",
                    "time_limit",
                ),
            },
        ),
    )
    ordering = ("name", "id")
    list_select_related = ("owner",)
    actions = [
        "upload_selected_problem",
    ]
    change_list_template = 'admin/problems/change_list.html'
    change_actions = ("update_problem_testcase", "update_problem_information")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        if request.user.is_superuser:
            return queryset

        return queryset.filter(owner=request.user)

    @admin.display(description="更新說明")
    def update_illustrate(self, *args, **kwargs):
        return mark_safe(
            f"""
                若是想新增、修改、刪除測試資料或者題目資訊請在操作完後按下 “儲存並繼續編輯”，
                再按下 ”更新測資“ 或者 ”更新題目資訊“ 即可將資料上傳至 domjudge。
            """
        )

    @action(label="更新測資", description="update inout")
    def update_problem_testcase(self, request, problem_obj):
        problem_log_obj_all = problem_obj.problem_log.all()

        if not problem_log_obj_all:
            return messages.error(request, "請先上傳題目！！")

        for problem_log_obj in problem_log_obj_all:

            server_user = DomServerUser.objects.get(owner=request.user, server_client=problem_log_obj.server_client)
            client_obj = server_user.server_client
            server_client = DomServerClientModel(
                host=client_obj.host,
                username=server_user.username,
                mask_password=server_user.mask_password,
            )
            try:
                problem_crawler = create_problem_crawler(server_client)
                web_testcases_all_dict = problem_crawler.get_testcases_all(
                    problem_id=problem_log_obj.web_problem_id
                )

                problems_testcases_all_dict = testcase_admin.handle_problem_testcase_data(problem_obj=problem_obj)
                (
                    web_testcases_difference,
                    web_testcases_retain,
                    problems_testcases_difference,
                ) = testcase_admin.handle_testcases_difference(
                    web_testcases_all_dict=web_testcases_all_dict,
                    problems_dict=problems_testcases_all_dict,
                )

                if problems_testcases_difference:
                    testcase_admin.create_not_exist_testcases(
                        problem_log_obj,
                        web_testcases_all_dict,
                        problems_testcases_all_dict,
                        problem_crawler,
                    )
                else:
                    testcase_admin.edit_exist_testcases(
                        problem_log_obj,
                        web_testcases_retain,
                        web_testcases_all_dict,
                        problems_testcases_all_dict,
                        problem_crawler,
                    )
                
                testcase_admin.handle_testcases_delete(
                    web_testcases_difference, web_testcases_all_dict, problem_crawler
                )

            except problem_exceptions.ProblemTestCaseUploadException as e:
                print(f"{type(e).__name__}:", e)
                return messages.error(request, str(e))
        
            messages.success(request, "測資更新成功！！")
        

    @action(label="更新題目資訊")
    def update_problem_information(self, request, obj):
        problem_name = obj.name
        problem_time_limit = obj.time_limit

        problem_info_data = {
            "problem[name]": problem_name,
            "problem[timelimit]": problem_time_limit,
        }

        problem_files = {"problem[problemtextFile]": obj.description_file}

        result_bool = True
        newest_problem_log = get_newest_problems_log(obj=obj)

        if not newest_problem_log:
            return messages.error(request, "請先上傳題目！！")

        for problem_log_obj in newest_problem_log:
            server_user = DomServerUser.objects.get(owner=request.user, server_client=problem_log_obj.server_client)
            client_obj = server_user.server_client
            server_client = DomServerClientModel(
                host=client_obj.host,
                username=server_user.username,
                mask_password=server_user.mask_password,
            )
            problem_crawler = create_problem_crawler(server_client)

            is_success = problem_crawler.update_problem_information(
                data=problem_info_data,
                files=problem_files,
                id=problem_log_obj.web_problem_id,
            )

            if not is_success:
                result_bool = False
                messages.error(
                    request,
                    f'{problem_log_obj.server_client.name} "{problem_log_obj.problem}" 更新錯誤！！',
                )
        if result_bool:
            messages.success(request, "題目資訊更新成功！！")

    def make_zip(self, obj, **kwargs):
        url = reverse_lazy("problem:zip", kwargs={"pk": str(obj.id)})
        return mark_safe(f'<a href="{url}">下載 zip</a>')

    make_zip.short_description = "下載壓縮檔"  # type: ignore

    def replacement_problem(self, obj, **kwargs):
        url = reverse_lazy("problem:check_zip", kwargs={"pk": str(obj.id)})
        return mark_safe(f'<a href="{url}">替換題目</a>')
    
    replacement_problem.short_description = "替換"  # type: ignore

    def save_model(self, request, obj, form, change):
        if not obj.owner_id:
            obj.owner = request.user

        super().save_model(request, obj, form, change)

    def upload_selected_problem(self, request, queryset):
        """
        Uploads the selected problem to a server.

        Args:
            request (HttpRequest): The HTTP request object.
            queryset (QuerySet): The selected problems to be uploaded.

        Returns:
            Return the selected problem to the upload_process.html page.
        """
        if request.user.is_superuser:
            server_users = DomServerUser.objects.all().order_by("server_client")
        else:
            server_users = DomServerUser.objects.filter(owner=request.user).order_by("id")

        if not server_users:
            return messages.error(request, "請先新增伺服器帳號連線資訊！！")
        
        servers_client_name = server_users.values_list("server_client__name", flat=True).distinct()
        servers_client_name_list = list()
        for obj in server_users:
            if obj.server_client.name not in servers_client_name_list:
                servers_client_name_list.append(obj.server_client.name)

        first_server_user = server_users[0]
        first_server_object = first_server_user.server_client

        if request.user.is_superuser:
            data = DomServerContest.objects.filter(server_client=first_server_object)
        else:
            data = DomServerContest.objects.filter(
                owner=request.user, server_client=first_server_object
            )
            
        contest_name = [(obj.short_name, obj.cid) for obj in data]

        if not request.user.is_superuser:
            demo_contest = DomServerContest.objects.filter(server_client=first_server_object, short_name="demo").first()
            contest_name.insert(0, (demo_contest.short_name, demo_contest.cid))

        server_client = DomServerClientModel(
            host=first_server_object.host,
            username=first_server_user.username,
            mask_password=first_server_user.mask_password,
        )

        problem_info = upload_problem_info_process(
            queryset=queryset, server_client=server_client
        )

        context = {
            "problem_info": problem_info,
            "servers_client_name": servers_client_name,
            "contest_name": contest_name,
            "opts": queryset.model._meta,
            "available_apps": get_available_apps(request),
        }

        return render(request, "upload_process.html", context)

    upload_selected_problem.short_description = "上傳所選的 題目"