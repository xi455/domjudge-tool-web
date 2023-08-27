from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET

from app.domservers.models.dom_server import DomServerClient

from .crawler import ProblemCrawler
from .models import DomServer, Problem
from .services.importer import build_zip_response


@require_GET
@login_required(login_url="/admin/login/")
@user_passes_test(lambda user: user.is_staff)
def get_zip(request, pk):
    obj = get_object_or_404(Problem, pk=pk)
    response = build_zip_response(obj)
    return response


def problem_view(request):

    if request.method == "POST":
        upload_objects = request.POST.getlist("upload_objects")
        domserver = request.POST.get("domserver")
        contests = request.POST.get("contests")

        domclient = get_object_or_404(DomServerClient, name=domserver)
        domserver_host = domclient.host
        domserver_user = domclient.username
        domserver_pwd = domclient.mask_password

        # print(domserver_host, domserver_user, domserver_pwd)
        problem_crawler = ProblemCrawler(domserver_host, domserver_user, domserver_pwd)

        upload_list = []
        upload_files = []

        for pk in upload_objects:
            obj = get_object_or_404(Problem, pk=pk)

            upload_list.append(obj)
            response_zip = build_zip_response(obj)

            # 將 StreamingHttpResponse 對象中的數據讀取為二進制內容
            content = b"".join(response_zip.streaming_content)
            upload_files.append(
                (
                    "problem_upload_multiple[archives][]",
                    (obj.name, content, "application/zip"),
                )
            )

        if upload_files:
            response, problem_id_list, option = problem_crawler.request_upload(
                files=upload_files, contests=contests
            )

            if response:
                for index in range(len(upload_list)):
                    upload_list[index].is_processed = True

                    domserver = DomServer(
                        problem=upload_list[index],
                        server_name=domserver,
                        problem_web_id=problem_id_list[index],
                        problem_web_contest=option,
                    )
                    domserver.save()

                # 使用 bulk_update 方法一次性更新多個物件
                Problem.objects.bulk_update(upload_list, ["is_processed"])

                messages.success(request, "題目上傳成功！！")
            else:
                messages.error(request, "題目名稱重複！！ 請重新命名或選擇新題目上傳")

    return redirect("/admin/problems/problem/")


def upload_view(obj, contests):
    pass


def update_view():
    pass
