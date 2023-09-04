import hashlib

from django.contrib import admin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django_object_actions import DjangoObjectActions, action
from pydantic import BaseModel

from app.domservers.models import DomServerClient

from .crawler import ProblemCrawler
from .models import DomServer, Problem, ProblemInOut
from django.contrib.auth.hashers import make_password, check_password


class ProblemTestCase(BaseModel):
    input: str
    out: str


class ProblemInOutInline(admin.TabularInline):
    model = ProblemInOut
    max_num = 10
    extra = 1


@admin.register(DomServer)
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
    readonly_fields = ("id", "owner", "inout_illustrate")
    fieldsets = (
        (
            None,
            {
                "fields": ("id", "owner", "inout_illustrate"),
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
    actions = ["upload_selected", "updown_selected"]
    change_actions = ("problem_inout_new_data", "problem_info_new_data")

    @admin.display(description="測資更新說明")
    def inout_illustrate(self, *args, **kwargs):
        return mark_safe(
            f"""
                若是想新增、修改、刪除測試資料或者題目資訊請在操作完後按下 “儲存並繼續編輯”，
                再按下 ”更新測資“ 或者 ”更新題目資訊“ 即可將資料上傳至 domjudge。
            """
        )

    @action(label="更新測資", description="update inout")
    def problem_inout_new_data(self, request, obj):
        problem_inout = obj.int_out_data.all()
        domserver = obj.domserver.all()

        for object in domserver:
            domclient = DomServerClient.objects.filter(name=object.server_name)

            url = domclient[0].host
            username = domclient[0].username
            password = domclient[0].mask_password

            problem_crawler = ProblemCrawler(url, username, password)
            testcases_dict = problem_crawler.request_testcases_get_all(
                problem_id=object.problem_web_id
            )
            problems_dict = {}

            for obj in problem_inout:
                problem_md5 = self.md5_hash(obj.input_content) + self.md5_hash(
                    obj.answer_content
                )

                info = {"input": obj.input_content, "out": obj.answer_content}

                problem_testcase = ProblemTestCase(**info)
                problems_dict[problem_md5] = problem_testcase

            testcases_md5 = set(testcases_dict.keys())
            problems_md5 = set(problems_dict.keys())

            problems_difference = problems_md5.difference(testcases_md5)
            testcases_difference = testcases_md5.difference(problems_md5)

            for md5 in testcases_difference:
                id = testcases_dict[md5].id
                problem_crawler.request_testcase_delete(id=id)

            for md5 in problems_difference:
                testcase_in, testcase_out = (
                    problems_dict[md5].input,
                    problems_dict[md5].out,
                )

                form_data = {}
                form_data["add_input"] = ("add.in", testcase_in)
                form_data["add_output"] = ("add.out", testcase_out)

                problem_crawler.request_update(
                    form_data=form_data, id=object.problem_web_id
                )

    @action(label="更新題目資訊", description="update problem info")
    def problem_info_new_data(self, request, obj):
        name = obj.name
        time_limit = obj.time_limit

        data = {}
        data["problem[name]"] = name
        data["problem[timelimit]"] = time_limit

        files = {}
        files["problem[problemtextFile]"] = obj.description_file

        domserver = obj.domserver.all()

        for object in domserver:
            domclient = DomServerClient.objects.filter(name=object.server_name)

            url = domclient[0].host
            username = domclient[0].username
            password = domclient[0].mask_password

            problem_crawler = ProblemCrawler(url, username, password)
            problem_crawler.request_problem_info_update(
                data=data, files=files, id=object.problem_web_id
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

    def md5_hash(self, testcase):
        encoded_string = testcase.encode("utf-8")
        md5_hash = hashlib.md5(encoded_string).hexdigest()

        return md5_hash

    def save_model(self, request, obj, form, change):
        if not obj.owner_id:
            obj.owner = request.user

        super().save_model(request, obj, form, change)

    def upload_selected(self, request, queryset):
        domserver_dict = {}
        domserver_accout = {}
        for object in DomServerClient.objects.all():

            domserver_dict[object.name] = object.host
            domserver_accout[object.name] = {
                "username": object.username,
                "password": object.mask_password,
            }

        domserver_keys = [key for key in domserver_dict.keys()]
        update_problem_name = {}
        process = False
        for query in queryset:

            if query.is_processed:
                process = True
                used_server_list = []

                for object in query.domserver.all():
                    used_server_list.append(
                        f"{object.server_name}({object.problem_web_contest})"
                    )

                if used_server_list:
                    update_problem_name[query.name] = ", ".join((used_server_list))

        field_name = ""
        if domserver_keys:
            host = domserver_dict[domserver_keys[0]]
            username = domserver_accout[domserver_keys[0]].get("username")
            password = domserver_accout[domserver_keys[0]].get("password")

            problem_crawler = ProblemCrawler(
                url=host, username=username, password=password
            )
            data = problem_crawler.request_contests_get_all()

            field_name = [field["formal_name"] for field in data]

        id_list = request.POST.getlist("_selected_action")
        upload_objects = Problem.objects.filter(id__in=id_list)

        context = {
            "process": process,
            "upload_objects": upload_objects,
            "update_problem_name": update_problem_name,
            "domserver": domserver_keys,
            "domserver_dict": domserver_dict,
            "field_name": field_name,
        }

        return render(request, "admin/upload_process.html", context)

    upload_selected.short_description = "上傳所選的 題目"

    def updown_selected(self, request, queryset):
        domclients = DomServerClient.objects.all()
        domclients_info = {}

        for domclient in domclients:
            domclients_info[domclient.name] = {
                "host": domclient.host,
                "username": domclient.username,
                "password": domclient.mask_password,
            }

        for query in queryset:
            query.is_processed = False

            problem_del = {}
            problem_domserver = query.domserver.all()
            for server in problem_domserver:
                if server.server_name not in problem_del:
                    problem_del[server.server_name] = server.problem_web_id

            for key, value in problem_del.items():
                host = domclients_info[key].get("host")
                username = domclients_info[key].get("username")
                password = domclients_info[key].get("password")

                problem_crawler = ProblemCrawler(
                    url=host,
                    username=username,
                    password=password,
                )

                problem_crawler.request_problem_delete(id=value)

        Problem.objects.bulk_update(queryset, ["is_processed"])

    updown_selected.short_description = "撤銷所選的 題目"
