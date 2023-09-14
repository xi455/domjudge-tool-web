import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_GET, require_http_methods

from app.domservers.models.dom_server import DomServerClient
from src.utils.admins import create_problem_crawler

from .forms import ServerClientForm
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
    upload_objects_id = request.POST.getlist("upload_objects_id")
    domserver_name = request.POST.get("domserver")
    contests_id = request.POST.get("contests")

    server_client = get_object_or_404(DomServerClient, name=domserver_name)

    problem_crawler = create_problem_crawler(server_client)

    upload_problem_obj_list = list()
    upload_files_info_list = list()
    upload_server_log_obj_list = list()

    update_server_log_obj_list = list()
    update_contest_problem_obj_list = list()
    update_contest_problem_info_dict = dict()

    contest_problem_count = problem_crawler.get_contest_problem_count(
        contest_id=contests_id
    )

    for pk in upload_objects_id:
        problem_obj = get_object_or_404(Problem, pk=pk)

        if problem_obj.is_processed:
            update_contest_problem_obj_list.append(problem_obj)
            update_contest_problem_info_dict.update(
                {
                    f"contest[problems][{contest_problem_count}][problem]": problem_obj.web_problem_id,
                    f"contest[problems][{contest_problem_count}][shortname]": problem_obj.short_name,
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
            contest_id=contests_id, problem_data=update_contest_problem_info_dict
        )
        if response is None:
            for index in range(len(update_contest_problem_obj_list)):
                web_problem_id = None
                update_problem_log_all = update_contest_problem_obj_list[
                    index
                ].problem_log.all()
                for problem_log_obj in update_problem_log_all:
                    if problem_log_obj.server_client == server_client:
                        web_problem_id = problem_log_obj.web_problem_id
                        break

                new_problem_log_obj = ProblemServerLog(
                    problem=update_contest_problem_obj_list[index],
                    server_client=server_client,
                    web_problem_contest=problem_crawler.get_contest_name(
                        contests_id=contests_id
                    ),
                    web_problem_id=web_problem_id,
                )
                update_server_log_obj_list.append(new_problem_log_obj)

            Problem.objects.bulk_update(upload_problem_obj_list, ["web_problem_id"])
            ProblemServerLog.objects.bulk_create(update_server_log_obj_list)

            messages.success(request, "題目更新成功！！")
        else:
            messages.error(request, "題目重複！！ 請重新選擇新題目上傳")

    if upload_files_info_list:
        (is_success, problem_id_list, contest_id,) = problem_crawler.upload_problem(
            files=upload_files_info_list, contest_id=contests_id
        )

        if is_success:
            for index in range(len(upload_problem_obj_list)):
                upload_problem_obj_list[index].is_processed = True
                upload_problem_obj_list[index].web_problem_id = problem_id_list[index]

                new_problem_log_obj = ProblemServerLog(
                    problem=upload_problem_obj_list[index],
                    server_client=server_client,
                    web_problem_id=problem_id_list[index],
                    web_problem_contest=problem_crawler.get_contest_name(contest_id),
                )

                upload_server_log_obj_list.append(new_problem_log_obj)

            Problem.objects.bulk_update(
                upload_problem_obj_list, ["is_processed", "web_problem_id"]
            )
            ProblemServerLog.objects.bulk_create(upload_server_log_obj_list)

            messages.success(request, "題目上傳成功！！")
        else:
            messages.error(request, "題目重複！！ 請重新選擇新題目上傳")
    return redirect("/admin/problems/problem/")


@require_http_methods(["POST"])
def problem_contest_view(request):
    problem_objects_id = request.POST.getlist("updown_objects_id")
    domserver_name = request.POST.get("domserver")
    contests_id = request.POST.get("contests")

    server_client = get_object_or_404(DomServerClient, name=domserver_name)
    problem_crawler = create_problem_crawler(server_client=server_client)

    for pk in problem_objects_id:
        problem_obj = get_object_or_404(Problem, pk=pk)
        problem_log_all = problem_obj.problem_log.all()

        for problem_log in problem_log_all:
            contest_name = problem_crawler.get_contest_name(contests_id=contests_id)

            if (
                problem_log.server_client.name == domserver_name
                and problem_log.web_problem_contest == contest_name
            ):
                is_success = problem_crawler.delete_contest_problem(
                    contest_id=contests_id,
                    web_problem_id=problem_log.web_problem_id,
                )

                if is_success:
                    messages.success(request, "考區題目移除成功！！")
                else:
                    messages.error(request, "此考區並未找到該題目！！")

                problem_log.delete()
                break

    return redirect("/admin/problems/problem/")


@require_http_methods(["POST"])
def contests_list_view(request):
    selected_contests_data = json.loads(request.body.decode("utf-8"))

    form = ServerClientForm(selected_contests_data)

    if form.is_valid():
        contest_name = form.cleaned_data.get("name", None)
        serverclient = get_object_or_404(DomServerClient, name=contest_name)
        problem_crawler = create_problem_crawler(server_client=serverclient)

        server_contests_info_dict = problem_crawler.get_contests_list_all()
        contests_data = {
            key: obj.conteset_id for key, obj in server_contests_info_dict.items()
        }

        return JsonResponse(contests_data)
    else:
        errors = form.errors
        return JsonResponse({"errors": errors}, status=400)
