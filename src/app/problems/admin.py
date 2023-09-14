from django.contrib import admin, messages
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django_object_actions import DjangoObjectActions, action
from pydantic import BaseModel

from app.domservers.models import DomServerClient
from src.utils.admins import (
    create_problem_crawler,
    testcase_md5,
)

from .forms import ProblemNameForm
from .models import Problem, ProblemInOut, ProblemServerLog


class ProblemTestCase(BaseModel):
    input: str
    out: str


class ProblemInOutInline(admin.TabularInline):
    model = ProblemInOut
    max_num = 10
    extra = 1


@admin.register(ProblemServerLog)
class DomserverAdmin(DjangoObjectActions, admin.ModelAdmin):
    pass


@admin.register(Problem)
class ProblemAdmin(DjangoObjectActions, admin.ModelAdmin):

    # form = ProblemNameForm

    list_display = (
        "short_name",
        "name",
        "time_limit",
        "owner",
        "id",
        "is_processed",
        "make_zip",
    )
    list_filter = ("create_at", "update_at")
    search_fields = ("name", "short_name")
    inlines = [ProblemInOutInline]
    readonly_fields = ("id", "owner", "update_illustrate", "web_problem_id")
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
                    "short_name",
                    "description_file",
                    "time_limit",
                    "web_problem_id",
                ),
            },
        ),
    )
    ordering = ("short_name", "name", "id")
    list_select_related = ("owner",)
    actions = [
        "upload_selected_problem",
        "updown_selected_problem",
        "updown_selected_contest",
    ]
    change_actions = ("update_problem_testcase", "update_problem_information")

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
        problem_testcase_obj_all = problem_obj.int_out_data.all()
        problem_log_obj_all = problem_obj.problem_log.all()

        is_success = None
        for problem_log_obj in problem_log_obj_all:
            server_client = problem_log_obj.server_client

            problem_crawler = create_problem_crawler(server_client)
            web_testcases_all_dict = problem_crawler.get_testcases_all(
                problem_id=problem_log_obj.web_problem_id
            )

            problems_dict = dict()
            for testcase_obj in problem_testcase_obj_all:
                problem_testcase_md5 = testcase_md5(
                    testcase_obj.input_content
                ) + testcase_md5(testcase_obj.answer_content)

                problem_testcase_info = {
                    "input": testcase_obj.input_content,
                    "out": testcase_obj.answer_content,
                }

                problem_testcase = ProblemTestCase(**problem_testcase_info)
                problems_dict[problem_testcase_md5] = problem_testcase

            web_testcases_md5 = set(web_testcases_all_dict.keys())
            problems_testcases_md5 = set(problems_dict.keys())

            problems_testcases_difference = problems_testcases_md5.difference(
                web_testcases_md5
            )
            web_testcases_difference = web_testcases_md5.difference(
                problems_testcases_md5
            )

            for web_md5 in web_testcases_difference:
                web_testcase_id = web_testcases_all_dict[web_md5].id
                problem_crawler.delete_testcase(id=web_testcase_id)

            for problem_md5 in problems_testcases_difference:
                testcase_in, testcase_out = (
                    problems_dict[problem_md5].input,
                    problems_dict[problem_md5].out,
                )

                problem_testcase_info_data = {
                    "add_input": ("add.in", testcase_in),
                    "add_output": ("add.out", testcase_out),
                }
                is_success = problem_crawler.update_testcase(
                    form_data=problem_testcase_info_data,
                    id=problem_log_obj.web_problem_id,
                )

        if is_success:
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

        problem_log_obj_all = obj.problem_log.all()

        for problem_log_obj in problem_log_obj_all:
            server_client = problem_log_obj.server_client
            problem_crawler = create_problem_crawler(server_client)

            is_success = problem_crawler.update_problem_information(
                data=problem_info_data,
                files=problem_files,
                id=problem_log_obj.web_problem_id,
            )

            if is_success:
                messages.success(
                    request,
                    f"{problem_log_obj.server_client.name}({problem_log_obj.web_problem_contest}) 更新成功！！",
                )
            else:
                messages.error(
                    request,
                    f"{problem_log_obj.server_client.name}({problem_log_obj.web_problem_contest}) 更新錯誤！！",
                )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(owner=request.user)
        return queryset

    def make_zip(self, obj, **kwargs):
        url = reverse_lazy("problem:zip", kwargs={"pk": str(obj.id)})
        return mark_safe(f'<a href="{url}">下載 zip</a>')

    make_zip.short_description = "下載壓縮檔"  # type: ignore

    def save_model(self, request, obj, form, change):
        if not obj.owner_id:
            obj.owner = request.user

        super().save_model(request, obj, form, change)

    def upload_selected_problem(self, request, queryset):
        dom_server_objects_all = DomServerClient.objects.all()
        dom_server_name = [obj.name for obj in dom_server_objects_all]

        used_contest_name_dict = dict()
        process = False
        for query in queryset:

            if query.is_processed:
                process = True
                problem_contest_info_list = list()

                for problem_log_object in query.problem_log.all():
                    problem_contest_info_list.append(
                        f"{problem_log_object.server_client}({problem_log_object.web_problem_contest})"
                    )

                if problem_contest_info_list:
                    used_contest_name_dict[query.name] = ", ".join(
                        problem_contest_info_list
                    )

        contest_name = None
        if dom_server_objects_all:
            problem_crawler = create_problem_crawler(dom_server_objects_all[0])
            data = problem_crawler.get_contests_list_all()

            contest_name = [(name, obj.conteset_id) for name, obj in data.items()]

        id_list = request.POST.getlist("_selected_action")
        upload_objects = Problem.objects.filter(id__in=id_list)

        context = {
            "process": process,
            "upload_objects": upload_objects,
            "update_problem_name": used_contest_name_dict,
            "dom_server_name": dom_server_name,
            "contest_name": contest_name,
        }

        return render(request, "admin/upload_process.html", context)

    upload_selected_problem.short_description = "上傳所選的 題目"

    def updown_selected_contest(self, request, queryset):
        id_list = request.POST.getlist("_selected_action")
        updown_contest_objects = Problem.objects.filter(id__in=id_list)

        update_problem_name_dict = dict()

        for query in queryset:
            problem_server_contest_info = []

            for problem_log_object in query.problem_log.all():
                problem_server_contest_info.append(
                    f"{problem_log_object.server_client}({problem_log_object.web_problem_contest})"
                )

            if problem_server_contest_info:
                update_problem_name_dict[query.name] = ", ".join(
                    problem_server_contest_info
                )

        server_clients = DomServerClient.objects.all()
        dom_server_name_list = [obj.name for obj in server_clients]

        problem_crawler = create_problem_crawler(server_client=server_clients[0])

        data = problem_crawler.get_contests_list_all()
        contest_name = {(name, obj.conteset_id) for name, obj in data.items()}

        context = {
            "updown_objects": updown_contest_objects,
            "update_problem_name": update_problem_name_dict,
            "domserver_name_list": dom_server_name_list,
            "field_name": contest_name,
        }

        return render(request, "admin/updown_process.html", context)

    updown_selected_contest.short_description = "撤銷所選的 考區"

    def updown_selected_problem(self, request, queryset):
        problem_del_info_dict = dict()
        for problem_obj in queryset:
            problem_obj.is_processed = False
            problem_obj.web_problem_id = None
            problem_log_all = problem_obj.problem_log.all()

            for problem_log in problem_log_all:
                server_client_obj = problem_log.server_client
                if server_client_obj not in problem_del_info_dict:
                    problem_del_info_dict[
                        server_client_obj
                    ] = problem_log.web_problem_id
                problem_log.delete()

        for obj, web_id in problem_del_info_dict.items():
            problem_crawler = create_problem_crawler(server_client=obj)
            problem_crawler.delete_problem(id=web_id)

        Problem.objects.bulk_update(queryset, ["is_processed", "web_problem_id"])

    updown_selected_problem.short_description = "撤銷所選的 題目"
