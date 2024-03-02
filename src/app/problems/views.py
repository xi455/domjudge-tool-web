import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_GET, require_http_methods

from app.domservers.models.dom_server import DomServerClient, DomServerContest
from app.users.models import User
from utils.admins import create_problem_crawler, upload_problem_info_process
from utils.problems.views import create_problem_log, handle_problems_upload_info

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
def problem_upload_view(request):
    problem_id_list = json.loads(request.POST.get("problemIdHidden"))
    domserver_name = request.POST.get("domserver")
    contest_id = request.POST.get("contests")

    owner_obj = get_object_or_404(User, username=request.user)
    server_client = get_object_or_404(DomServerClient, name=domserver_name)
    contest_obj = DomServerContest.objects.filter(
        server_client=server_client, cid=contest_id
    ).first()
    problem_crawler = create_problem_crawler(server_client)

    problem_data = {
        "problem_id_list": problem_id_list,
        "owner_obj": owner_obj,
        "server_client": server_client,
        "contest_obj": contest_obj,
    }

    problems_upload_info, problems_obj_data_dict = handle_problems_upload_info(
        problem_data=problem_data
    )

    (
        is_success,
        problems_info_dict,
        contest_id,
        message,
    ) = problem_crawler.upload_problem(
        files=problems_upload_info, contest_id=contest_id
    )

    if not is_success:
        messages.error(request, message)
        return redirect("/admin/problems/problem/")
    messages.success(request, message)

    for pname, pid in problems_info_dict.items():
        problems_obj_data_dict[pname].update({"web_problem_id": pid})

    create_problem_log(problems_obj_data_dict=problems_obj_data_dict)

    return redirect("/admin/problems/problem/")


@require_http_methods(["POST"])
def problem_contest_view(request):
    problem_objects_id = request.POST.getlist("updown_objects_id")
    domserver_name = request.POST.get("domserver")
    contests_id = request.POST.get("contests")

    server_client = get_object_or_404(DomServerClient, name=domserver_name)
    problem_crawler = create_problem_crawler(server_client=server_client)
    contest_name = problem_crawler.get_contest_name(contests_id=contests_id)

    for pk in problem_objects_id:
        problem_obj = get_object_or_404(Problem, pk=pk)
        problem_log_all = problem_obj.problem_log.all().order_by("-id")

        upload_server_log_obj_list = list()
        for problem_log in problem_log_all:

            if (
                problem_log.server_client.name == domserver_name
                and problem_log.web_problem_contest == contest_name
                and problem_log.web_problem_state == "新增"
            ):
                is_success = problem_crawler.delete_contest_problem(
                    contest_id=contests_id,
                    web_problem_id=problem_log.web_problem_id,
                )

                if is_success:
                    new_problem_log_obj = ProblemServerLog(
                        problem=problem_log.problem,
                        server_client=problem_log.server_client,
                        web_problem_id=problem_log.web_problem_id,
                        web_problem_state="移除",
                        web_problem_contest=problem_log.web_problem_contest,
                    )
                    upload_server_log_obj_list.append(new_problem_log_obj)
                    ProblemServerLog.objects.bulk_create(upload_server_log_obj_list)

                    messages.success(request, "考區題目移除成功！！")
                else:
                    messages.error(request, "此考區並未找到該題目！！")
                break

    return redirect("/admin/problems/problem/")


@require_http_methods(["POST"])
def get_contests_info_and_problem_info_api(request):
    """
    View function to retrieve contests data and upload problem information.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        JsonResponse: The JSON response containing contests data and upload problem information.
    """

    data = json.loads(request.body.decode("utf-8"))
    server_name_dict = data["serverNameDict"]
    problem_id_list = data["problemIDArray"]

    # __in 是 Django ORM 的一種查詢過濾器（Query Filter），它接受一個列表，並返回一個包含所有在該列表中的值的對象的 QuerySet。

    form = ServerClientForm(server_name_dict)

    if form.is_valid():
        queryset = Problem.objects.filter(id__in=problem_id_list)
        server_object = get_object_or_404(
            DomServerClient, name=server_name_dict["name"]
        )
        upload_problem_info = upload_problem_info_process(
            queryset=queryset, server_object=server_object
        )

        contest_name = form.cleaned_data.get("name", None)
        serverclient = get_object_or_404(DomServerClient, name=contest_name)
        problem_crawler = create_problem_crawler(server_client=serverclient)

        server_contests_info_dict = problem_crawler.get_contests_list_all()
        contests_data = {
            key: obj.contest_id for key, obj in server_contests_info_dict.items()
        }

        response_data = {
            "contests_data": contests_data,
            "upload_problem_info": upload_problem_info,
        }

        return JsonResponse(response_data, status=200)
    else:
        errors = form.errors
        return JsonResponse({"errors": errors}, status=400)
