from django.contrib import admin, messages
from django.http import HttpRequest
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django_object_actions import DjangoObjectActions, action
from pydantic import BaseModel

from app.domservers.models import DomServerClient, DomServerContest
from utils.admins import (
    create_problem_crawler,
    get_newest_problems_log,
    testcase_md5,
    upload_problem_info_process,
)
from utils.views import get_available_apps

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
    list_display = (
        "owner",
        "problem",
        "server_client",
        "web_problem_id",
        "contest",
        "web_problem_state",
    )


@admin.register(Problem)
class ProblemAdmin(DjangoObjectActions, admin.ModelAdmin):

    # form = ProblemNameForm

    list_display = (
        "name",
        "short_name",
        "time_limit",
        "owner",
        "id",
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

    def handle_problem_testcase_data(self, problem_obj):
        """
        Handle the problem testcase data.

        Args:
            problem_obj (Problem): The problem object.

        Returns:
            dict: A dictionary containing the problem testcases.
        """
        problem_testcase_obj_all = problem_obj.int_out_data.all()

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

        return problems_dict

    def handle_testcases_difference(self, web_testcases_all_dict, problems_dict):
        """
        Handle the testcases difference.

        Returns:
            Tuple[set, set]: The difference between the testcases.
        """
        web_testcases_md5 = set(web_testcases_all_dict.keys())
        problems_testcases_md5 = set(problems_dict.keys())

        problems_testcases_difference = problems_testcases_md5.difference(
            web_testcases_md5
        )
        web_testcases_difference = web_testcases_md5.difference(problems_testcases_md5)

        return web_testcases_difference, problems_testcases_difference

    def handle_testcases_delete(
        self, web_testcases_difference, web_testcases_all_dict, problem_crawler
    ):
        """
        Delete test cases from the problem crawler based on the given web_testcases_difference.

        Args:
            web_testcases_difference (list): List of MD5 hashes representing the test cases to be deleted.
            web_testcases_all_dict (dict): Dictionary containing testcase MD5 hashes as keys and corresponding input/output test cases as values.
            problem_crawler (ProblemCrawler): Object used to delete test cases.

        Returns:
            None
        """
        for web_md5 in web_testcases_difference:
            web_testcase_id = web_testcases_all_dict[web_md5].id
            problem_crawler.delete_testcase(id=web_testcase_id)

    def handle_testcases_upload(
        self,
        problems_testcases_difference,
        problems_dict,
        problem_log_obj,
        problem_crawler,
    ):
        """
        Handles the upload of test cases for a problem.

        Args:
            problems_testcases_difference (list): List of problem MD5 hashes for which test cases need to be uploaded.
            problems_dict (dict): Dictionary containing testcase MD5 hashes as keys and corresponding input/output test cases as values.
            problem_log_obj (object): Object representing the problem log.
            problem_crawler (object): Object used to update test cases.

        Returns:
            bool: True if the test cases are successfully uploaded, False otherwise.
        """
        for problem_md5 in problems_testcases_difference:
            testcase_in, testcase_out = (
                problems_dict[problem_md5].input,
                problems_dict[problem_md5].out,
            )
            problem_testcase_info_data = {
                "add_input": ("add.in", testcase_in),
                "add_output": ("add.out", testcase_out),
            }
            result = problem_crawler.update_testcase(
                form_data=problem_testcase_info_data,
                id=problem_log_obj.web_problem_id,
            )

            if not result:
                return False

        return True

    def handle_testcases_edit(
        self,
        web_testcases_difference,
        web_testcases_all_dict,
        problems_testcases_difference,
        problems_dict,
        problem_log_obj,
        problem_crawler,
    ):
        """
        Edit the test cases for a problem.

        Args:
            web_testcases_difference (list): List of MD5 hashes representing the test cases to be deleted.
            web_testcases_all_dict (dict): Dictionary containing testcase MD5 hashes as keys and corresponding input/output test cases as values.
            problems_testcases_difference (list): List of problem MD5 hashes for which test cases need to be uploaded.
            problems_dict (dict): Dictionary containing testcase MD5 hashes as keys and corresponding input/output test cases as values.
            problem_log_obj (object): Object representing the problem log.
            problem_crawler (object): Object used to update test cases.

        Returns:
            bool: True if the test cases are edited successfully, False otherwise.
        """
        self.handle_testcases_delete(
            web_testcases_difference, web_testcases_all_dict, problem_crawler
        )
        return self.handle_testcases_upload(
            problems_testcases_difference,
            problems_dict,
            problem_log_obj,
            problem_crawler,
        )

    @action(label="更新測資", description="update inout")
    def update_problem_testcase(self, request, problem_obj):
        problem_log_obj_all = problem_obj.problem_log.all()

        for problem_log_obj in problem_log_obj_all:
            server_client = problem_log_obj.server_client

            problem_crawler = create_problem_crawler(server_client)
            web_testcases_all_dict = problem_crawler.get_testcases_all(
                problem_id=problem_log_obj.web_problem_id
            )

            problems_dict = self.handle_problem_testcase_data(problem_obj=problem_obj)
            (
                web_testcases_difference,
                problems_testcases_difference,
            ) = self.handle_testcases_difference(
                web_testcases_all_dict=web_testcases_all_dict,
                problems_dict=problems_dict,
            )

            edit_result = self.handle_testcases_edit(
                web_testcases_difference=web_testcases_difference,
                web_testcases_all_dict=web_testcases_all_dict,
                problems_testcases_difference=problems_testcases_difference,
                problems_dict=problems_dict,
                problem_log_obj=problem_log_obj,
                problem_crawler=problem_crawler,
            )

        if edit_result:
            messages.success(request, "測資更新成功！！")
        else:
            messages.error(request, "測資更新錯誤！！")

    @action(label="更新題目資訊")
    def update_problem_information(self, request, obj):
        problem_name = obj.name
        problem_time_limit = obj.time_limit

        problem_info_data = {
            "problem[name]": problem_name,
            "problem[timelimit]": problem_time_limit,
        }

        problem_files = {"problem[problemtextFile]": obj.description_file}

        newest_problem_log = get_newest_problems_log(obj=obj)
        for problem_log_obj in newest_problem_log:
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
                    f'{problem_log_obj.server_client.name} "{problem_log_obj.problem}" 更新成功！！',
                )
            else:
                messages.error(
                    request,
                    f'{problem_log_obj.server_client.name} "{problem_log_obj.problem}" 更新錯誤！！',
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
        """
        Uploads the selected problem to a server.

        Args:
            request (HttpRequest): The HTTP request object.
            queryset (QuerySet): The selected problems to be uploaded.

        Returns:
            Return the selected problem to the upload_process.html page.
        """
        if request.user.is_superuser:
            server_objects = DomServerClient.objects.all().order_by("id")
        else:
            server_objects = DomServerClient.objects.filter(owner=request.user).order_by(
                "id"
            )

        if not server_objects:
            return messages.error(request, "請先新增伺服器資訊！！")

        first_server_object = server_objects[0]

        if request.user.is_superuser:
            data = DomServerContest.objects.filter(server_client=first_server_object)
        else:
            data = DomServerContest.objects.filter(
                owner=request.user, server_client=first_server_object
            )
        contest_name = [(obj.short_name, obj.cid) for obj in data]

        problem_info = upload_problem_info_process(
            queryset=queryset, server_object=first_server_object
        )

        context = {
            "problem_info": problem_info,
            "servers_client_name": [obj.name for obj in server_objects],
            "contest_name": contest_name,
            "opts": queryset.model._meta,
            "available_apps": get_available_apps(request),
        }

        return render(request, "upload_process.html", context)

    upload_selected_problem.short_description = "上傳所選的 題目"

    def updown_selected_contest(self, request, queryset):
        id_list = request.POST.getlist("_selected_action")
        updown_contest_objects = Problem.objects.filter(id__in=id_list)

        update_problem_name_dict = dict()

        for query in queryset:
            problem_server_contest_info = list()
            problem_log_all = query.problem_log.all().order_by("-id")

            contest_name_list = list()
            for problem_log_object in problem_log_all:

                if problem_log_object.web_problem_contest not in contest_name_list:
                    contest_name_list.append(problem_log_object.web_problem_contest)

                    if problem_log_object.web_problem_state == "新增":
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
        contest_name = {(name, obj.contest_id) for name, obj in data.items()}

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
        upload_server_log_obj_list = list()

        for problem_obj in queryset:
            problem_log_all = problem_obj.problem_log.all().order_by("-id")

            del_problem_id_list = list()
            contest_name_list = list()
            for problem_log in problem_log_all:
                server_client_obj = problem_log.server_client
                if server_client_obj not in problem_del_info_dict:
                    problem_del_info_dict[server_client_obj] = del_problem_id_list

                if problem_log.web_problem_contest not in contest_name_list:
                    contest_name_list.append(problem_log.web_problem_contest)

                    if problem_log.web_problem_state == "新增":
                        problem_del_info_dict[server_client_obj].append(problem_log)
                # problem_log.delete()

        for server_client_obj, problem_log_obj_list in problem_del_info_dict.items():
            for problem_log_obj in problem_log_obj_list:
                new_problem_log_obj = ProblemServerLog(
                    problem=problem_log_obj.problem,
                    server_client=problem_log_obj.server_client,
                    web_problem_id=problem_log_obj.web_problem_id,
                    web_problem_state="移除",
                    web_problem_contest=problem_log_obj.web_problem_contest,
                )

                upload_server_log_obj_list.append(new_problem_log_obj)

            # ## 新增
            ProblemServerLog.objects.bulk_create(upload_server_log_obj_list)

        print(problem_del_info_dict)
        # ------------------------------------------------------------
        for server_client_obj, problem_log_obj_list in problem_del_info_dict.items():
            problem_crawler = create_problem_crawler(server_client=server_client_obj)

            for problem_log_obj in problem_log_obj_list:
                problem_crawler.delete_problem(id=problem_log_obj.web_problem_id)

    updown_selected_problem.short_description = "撤銷所選的 題目"
