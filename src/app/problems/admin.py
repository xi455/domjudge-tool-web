from django.contrib import admin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django_object_actions import DjangoObjectActions, action
from pydantic import BaseModel

from app.domservers.models import DomServerClient
from src.utils.admins import testcase_md5, server_clients_all_information

from .crawler import ProblemCrawler
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
                    "short_name",
                    "description_file",
                    "time_limit",
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
    def update_problem_testcase(self, request, testcase_obj):
        problem_testcase_obj_all = testcase_obj.int_out_data.all()
        problem_log_obj_all = testcase_obj.problem_log.all()

        for problem_log_obj in problem_log_obj_all:
            server_client = problem_log_obj.server_client

            url = server_client.host
            username = server_client.username
            password = server_client.mask_password

            problem_crawler = ProblemCrawler(url, username, password)
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
                problem_crawler.update_testcase(
                    form_data=problem_testcase_info_data,
                    id=problem_log_obj.web_problem_id,
                )

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

            url = server_client.host
            username = server_client.username
            password = server_client.mask_password

            problem_crawler = ProblemCrawler(url, username, password)
            problem_crawler.update_problem_information(
                data=problem_info_data,
                files=problem_files,
                id=problem_log_obj.web_problem_id,
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
        domserver_dict = {}
        domserver_accout = {}
        for server_object in DomServerClient.objects.all():

            domserver_dict[server_object.name] = server_object.host
            domserver_accout[server_object.name] = {
                "username": server_object.username,
                "password": server_object.mask_password,
            }

        domserver_name_list = [key for key in domserver_dict.keys()]
        update_problem_name = dict()
        process = False
        for query in queryset:

            if query.is_processed:
                process = True
                problem_server_contest_info = []

                for problem_log_object in query.problem_log.all():
                    problem_server_contest_info.append(
                        f"{problem_log_object.server_client}({problem_log_object.web_problem_contest})"
                    )

                if problem_server_contest_info:
                    update_problem_name[query.name] = ", ".join(
                        problem_server_contest_info
                    )

        field_name = ""
        if domserver_name_list:
            host = domserver_dict[domserver_name_list[0]]
            username = domserver_accout[domserver_name_list[0]].get("username")
            password = domserver_accout[domserver_name_list[0]].get("password")

            problem_crawler = ProblemCrawler(
                url=host, username=username, password=password
            )
            data = problem_crawler.get_contests_all()

            field_name = [field["formal_name"] for field in data]

        id_list = request.POST.getlist("_selected_action")
        upload_objects = Problem.objects.filter(id__in=id_list)

        context = {
            "process": process,
            "upload_objects": upload_objects,
            "update_problem_name": update_problem_name,
            "domserver_name_list": domserver_name_list,
            "domserver_dict": domserver_dict,
            "field_name": field_name,
        }

        return render(request, "admin/upload_process.html", context)

    upload_selected_problem.short_description = "上傳所選的 題目"

    def updown_selected_problem(self, request, queryset):
        server_clients_information = server_clients_all_information()

        for problem_obj in queryset:
            problem_obj.is_processed = False

            problem_log_del_dict = dict()
            problem_log_obj_all = problem_obj.problem_log.all()
            for problem_log_obj in problem_log_obj_all:
                if problem_log_obj.server_client not in problem_log_del_dict:
                    problem_log_del_dict[
                        problem_log_obj.server_client
                    ] = problem_log_obj.web_problem_id

            for client, web_problem_id in problem_log_del_dict.items():
                host = server_clients_information[client.name].get("host")
                username = server_clients_information[client.name].get("username")
                password = server_clients_information[client.name].get("password")

                problem_crawler = ProblemCrawler(
                    url=host,
                    username=username,
                    password=password,
                )

                problem_crawler.delete_problem(id=web_problem_id)
            problem_log_obj_all.delete()
        Problem.objects.bulk_update(queryset, ["is_processed"])

    updown_selected_problem.short_description = "撤銷所選的 題目"

    def updown_selected_contest(self, request, queryset):
        domclients_info = server_clients_all_information()
        queryset_list = []

        for query in queryset:
            problem_contests_info = query.domserver.all()
            for contest in problem_contests_info:
                if "contest_set" in domclients_info[contest.server_name]:
                    domclients_info[contest.server_name]["contest_set"].add(
                        contest.problem_web_contest
                    )
                else:
                    domclients_info[contest.server_name]["contest_set"] = set()
                    domclients_info[contest.server_name]["contest_set"].add(
                        contest.problem_web_contest
                    )

        print(domclients_info)
        context = {}

        # return render(request, "admin/updown_process.html", context)

    updown_selected_contest.short_description = "撤銷所選的 考區"
