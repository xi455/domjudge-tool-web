from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_GET, require_http_methods

from app.domservers.models.dom_server import DomServerClient

from .crawler import ProblemCrawler
from .models import Problem, ProblemServerLog
from .services.importer import build_zip_response


@require_GET
@login_required(login_url="/admin/login/")
@user_passes_test(lambda user: user.is_staff)
def get_zip(request, pk):
    obj = get_object_or_404(Problem, pk=pk)
    response = build_zip_response(obj)
    return response


@require_http_methods(["POST"])
def problem_view(request):
    upload_objects = request.POST.getlist("upload_objects")
    domserver_name = request.POST.get("domserver")
    contests_name = request.POST.get("contests")

    domserver_client = get_object_or_404(DomServerClient, name=domserver_name)

    host = domserver_client.host
    username = domserver_client.username
    password = domserver_client.mask_password

    problem_crawler = ProblemCrawler(
        url=host,
        username=username,
        password=password,
    )

    upload_problem_obj_list = list()
    upload_files_info_list = list()
    upload_server_log_obj_list = list()
    update_server_log_obj_list = list()
    update_contest_problem_obj_list = list()
    update_contest_problem_info_dict = dict()

    contest_problem_count = problem_crawler.get_contest_problem_count(
        contest=contests_name
    )

    for pk in upload_objects:
        problem_obj = get_object_or_404(Problem, pk=pk)

        is_problem_update = False
        problem_log_obj = None
        for problem_log_obj in problem_obj.problem_log.all():
            if domserver_client == problem_log_obj.server_client:
                is_problem_update = True
                break

        if is_problem_update:
            update_contest_problem_obj_list.append(problem_obj)
            update_contest_problem_info_dict.update(
                {
                    f"contest[problems][{contest_problem_count}][problem]": problem_log_obj.web_problem_id,
                    f"contest[problems][{contest_problem_count}][shortname]": problem_log_obj.web_problem_shortname,
                    f"contest[problems][{contest_problem_count}][points]": "1",
                    f"contest[problems][{contest_problem_count}][allowSubmit]": "1",
                    f"contest[problems][{contest_problem_count}][allowJudge]": "1",
                    f"contest[problems][{contest_problem_count}][color]": "",
                    f"contest[problems][{contest_problem_count}][lazyEvalResults]": "0",
                }
            )
            contest_problem_count += 1
        else:
            upload_problem_obj_list.append(problem_obj)
            response_zip = build_zip_response(problem_obj)

            content = b"".join(response_zip.streaming_content)
            upload_files_info_list.append(
                (
                    "problem_upload_multiple[archives][]",
                    (problem_obj.name, content, "application/zip"),
                )
            )

    if update_contest_problem_info_dict:
        response = problem_crawler.contest_problem_upload(
            contest=contests_name, problem_data=update_contest_problem_info_dict
        )
        if response:
            for index in range(len(update_contest_problem_obj_list)):
                web_problem_id = None
                for problem_log_obj in update_contest_problem_obj_list[
                    index
                ].problem_log.all():
                    if problem_log_obj.server_client == domserver_client:
                        web_problem_id = problem_log_obj.web_problem_id
                        break

                server_log_obj = ProblemServerLog(
                    problem=update_contest_problem_obj_list[index],
                    server_client=domserver_client,
                    web_problem_id=web_problem_id,
                    web_problem_shortname=update_contest_problem_obj_list[
                        index
                    ].short_name,
                    web_problem_contest=contests_name,
                )
                update_server_log_obj_list.append(server_log_obj)

            Problem.objects.bulk_update(upload_problem_obj_list, ["is_processed"])
            ProblemServerLog.objects.bulk_create(update_server_log_obj_list)

            messages.success(request, "題目更新成功！！")
        else:
            messages.error(request, "題目重複！！ 請重新選擇新題目上傳")

    if upload_files_info_list:
        (is_success, problem_id_list, contest_id,) = problem_crawler.upload_problem(
            files=upload_files_info_list, contests=contests_name
        )

        if is_success:
            for index in range(len(upload_problem_obj_list)):
                upload_problem_obj_list[index].is_processed = True

                server_log_obj = ProblemServerLog(
                    problem=upload_problem_obj_list[index],
                    server_client=domserver_client,
                    web_problem_id=problem_id_list[index],
                    # web_problem_shortname=upload_problem_obj_list[index].short_name,
                    web_problem_shortname=upload_problem_obj_list[index].name,
                    web_problem_contest=contests_name,
                )

                upload_server_log_obj_list.append(server_log_obj)

            Problem.objects.bulk_update(upload_problem_obj_list, ["is_processed"])
            ProblemServerLog.objects.bulk_create(upload_server_log_obj_list)

            messages.success(request, "題目上傳成功！！")
        else:
            messages.error(request, "題目重複！！ 請重新選擇新題目上傳")
    return redirect("/admin/problems/problem/")
