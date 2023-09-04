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
        domserver_name = request.POST.get("domserver")
        contests = request.POST.get("contests")

        domclient = get_object_or_404(DomServerClient, name=domserver_name)

        host = domclient.host
        username = domclient.username
        password = domclient.mask_password

        problem_crawler = ProblemCrawler(
            url=host,
            username=username,
            password=password,
        )

        upload_list = []
        upload_files = []
        upload_content = {}
        upload_content_list = []

        contest_problem_count = problem_crawler.request_contest_problem_count(
            contest=contests
        )

        for pk in upload_objects:
            obj = get_object_or_404(Problem, pk=pk)

            is_problem = False
            object = None
            for object in obj.domserver.all():
                if domserver_name == object.server_name:
                    is_problem = True
                    break

            if is_problem:
                upload_content_list.append(obj)
                upload_content.update(
                    {
                        f"contest[problems][{contest_problem_count}][problem]": object.problem_web_id,
                        f"contest[problems][{contest_problem_count}][shortname]": object.problem_shortname,
                        f"contest[problems][{contest_problem_count}][points]": "1",
                        f"contest[problems][{contest_problem_count}][allowSubmit]": "1",
                        f"contest[problems][{contest_problem_count}][allowJudge]": "1",
                        f"contest[problems][{contest_problem_count}][color]": "",
                        f"contest[problems][{contest_problem_count}][lazyEvalResults]": "0",
                    }
                )
                contest_problem_count += 1
            else:
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

        if upload_content:
            response = problem_crawler.request_contest_problem_upload(
                contest=contests, problem_data=upload_content
            )
            if response:
                for index in range(len(upload_content_list)):
                    problem_web_id = None
                    for object in upload_content_list[index].domserver.all():
                        if object.server_name == domserver_name:
                            problem_web_id = object.problem_web_id
                            break
                    domserver = DomServer(
                        problem=upload_content_list[index],
                        server_name=domserver_name,
                        problem_web_id=problem_web_id,
                        problem_shortname=upload_content_list[index].short_name,
                        problem_web_contest=contests,
                    )
                    domserver.save()
                #
                # 使用 bulk_update 方法一次性更新多個物件
                Problem.objects.bulk_update(upload_list, ["is_processed"])

                messages.success(request, "題目更新成功！！")
            else:
                messages.error(request, "題目重複！！ 請重新選擇新題目上傳")

        if upload_files:
            (
                response,
                problem_id_list,
                contest_id,
            ) = problem_crawler.request_upload(files=upload_files, contests=contests)

            if response:
                for index in range(len(upload_list)):
                    upload_list[index].is_processed = True

                    domserver = DomServer(
                        problem=upload_list[index],
                        server_name=domserver_name,
                        problem_web_id=problem_id_list[index],
                        problem_shortname=upload_list[index].short_name,
                        problem_web_contest=contests,
                    )
                    domserver.save()

                # 使用 bulk_update 方法一次性更新多個物件
                Problem.objects.bulk_update(upload_list, ["is_processed"])

                messages.success(request, "題目上傳成功！！")
            else:
                messages.error(request, "題目重複！！ 請重新選擇新題目上傳")
    return redirect("/admin/problems/problem/")
