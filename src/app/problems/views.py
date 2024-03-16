import json

from django.db import transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from app.users.models import User
from app.problems.unzip import handle_upload_required_file, handle_unzip_problem_obj
from app.domservers.models.dom_server import DomServerClient, DomServerContest

from utils.views import get_available_apps
from utils.admins import create_problem_crawler, upload_problem_info_process
from utils.problems.views import create_problem_log, handle_problems_upload_info, handle_problem_upload_format

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

@transaction.atomic
def replace_logs_and_create_problem(request, problem_log_objs, new_problem_obj):
    problem_client_data = dict()
    updated_logs_obj = list()
    upload_problem_file_info = handle_problem_upload_format(new_problem_obj)
    
    for log in problem_log_objs:
        if log.server_client not in problem_client_data:
            problem_crawler = create_problem_crawler(log.server_client)

            (
                is_success,
                problems_info_dict,
                contest_id,
            ) = problem_crawler.upload_problem(
                files=[upload_problem_file_info], contest_id=log.contest.cid,
            )

            if not is_success:
                return redirect("/admin/problems/problem/")

            problem_client_data[log.server_client] = {
                "old_pid": log.web_problem_id,
                "pid": problems_info_dict[new_problem_obj.name],
                "cid": list(),
            }
        else:
            problem_client_data[log.server_client]["cid"].append(log.contest.cid)
        
        log.problem = new_problem_obj
        log.web_problem_id = problem_client_data[log.server_client]["pid"]
        updated_logs_obj.append(log)

    ProblemServerLog.objects.bulk_update(updated_logs_obj, ['problem', 'web_problem_id'])

    return problem_client_data


def update_dj_contest_info_for_replace_problem(request, problem_log_objs, new_problem_obj):
    problem_client_data = replace_logs_and_create_problem(request, problem_log_objs, new_problem_obj)
        
    for obj, value in problem_client_data.items():
        problem_crawler = create_problem_crawler(obj)
        problem_crawler.delete_problem(request, value["old_pid"])

        for cid in value["cid"]:
            problem_data_info = problem_crawler.get_contest_problems_info(cid)
            problem_data_info.append({
                "id": value["pid"],
                "name": new_problem_obj.name,
            })

            contest_info = problem_crawler.get_contest_or_problem_information(cid, need_content="contest")
            
            # 需在取得原有的problem資料
            problem_format_info = problem_crawler.problem_format_process(problem_data_info)

            contest_info.update(problem_format_info)

            result = problem_crawler.contest_problem_upload(cid, contest_info)

            if not result:
                messages.error(request, f"考區 {obj.name} 題目取代失敗！！")
                return redirect("/admin/problems/problem/")

    messages.success(request, f"考區題目取代成功！！")
    return redirect("/admin/problems/problem/")
    

@transaction.atomic
@login_required(login_url="/admin/login/")
def upload_zip_view(request, pk=None):
    available_apps = get_available_apps(request)
    opts = Problem._meta

    if request.method == "POST":
        files = request.FILES.getlist('file')

        try:
            if pk is None:
                for file in files:
                    # Get required file information
                    file_info_dict = handle_upload_required_file(file)
                
                    # Create problem object and problem in/out object
                    handle_unzip_problem_obj(request, file_info_dict)

            if pk is not None:
                # files[0] is the first file in the list
                file_info_dict = handle_upload_required_file(files[0])

                # Create problem object and problem in/out object
                new_problem_obj = handle_unzip_problem_obj(request, file_info_dict)

                problem = get_object_or_404(Problem, pk=pk)
                problem_log_objs = problem.problem_log.all()
                if problem_log_objs:
                    # Replace problem object in problem log
                    update_dj_contest_info_for_replace_problem(request, problem_log_objs, new_problem_obj)
                
                problem.delete() 

        except Exception as e:
            print(f"{type(e).__name__}:", e)
            
        return redirect("/admin/problems/problem/")

    if request.method == "GET":
        context = {
            "opts": opts,
            "available_apps": available_apps,
        }
        return render(request, "upload_zip.html", context)


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
    ) = problem_crawler.upload_problem(
        files=problems_upload_info, contest_id=contest_id
    )

    if not is_success:
        return redirect("/admin/problems/problem/")

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

        if request.user.is_superuser:
            server_contests_info_dict = DomServerContest.objects.filter(
                server_client=serverclient
            )
        else:
            server_contests_info_dict = DomServerContest.objects.filter(
                owner=request.user, server_client=serverclient
            )

        contests_data = {
            obj.short_name: obj.cid for obj in server_contests_info_dict
        }

        response_data = {
            "contests_data": contests_data,
            "upload_problem_info": upload_problem_info,
        }

        return JsonResponse(response_data, status=200)
    else:
        errors = form.errors
        return JsonResponse({"errors": errors}, status=400)


def check_zip_view(request, pk):
    problem = get_object_or_404(Problem, pk=pk)
    available_apps = get_available_apps(request)

    if request.method == "POST":
        return redirect("problem:upload_zip_with_pk", pk = problem.id)

    if request.method == "GET":

        context = {
            "obj": problem,
            "opts": Problem._meta,
            "available_apps": available_apps,

        }
        return render(request, "check_zip.html", context)