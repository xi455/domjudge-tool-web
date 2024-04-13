import json

from django.db import transaction
from django.contrib import messages
from django.http import JsonResponse
from django.core.validators import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test

from app.domservers.models.dom_server import DomServerClient, DomServerUser, DomServerContest

from utils.views import get_available_apps
from utils.admins import create_problem_crawler
from utils.problems.admin import upload_problem_info_process
from utils.problems.views import create_problem_log, handle_problems_upload
from utils.validator_pydantic import DomServerClientModel

from app.problems.models import Problem
from app.problems.forms import ServerClientForm

from app.problems.views.unzip import handle_upload_required_file, handle_unzip_problem_obj
from app.problems.services.importer import build_zip_response
from app.problems.views.replace_problems import update_dj_contest_info_for_replace_problem

from app.problems import exceptions as problem_exceptions

@require_GET
@login_required(login_url="/admin/login/")
@user_passes_test(lambda user: user.is_staff)
def get_zip(request, pk):
    obj = get_object_or_404(Problem, pk=pk)
    response = build_zip_response(obj)
    return response

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
                    file_info_obj = handle_upload_required_file(request, file)
                
                    # Create problem object and problem in/out object
                    handle_unzip_problem_obj(request, file_info_obj)

            if pk is not None:
                # files[0] is the first file in the list
                file_info_obj = handle_upload_required_file(request, files[0])

                # Create problem object and problem in/out object
                new_problem_obj = handle_unzip_problem_obj(request, file_info_obj)

                problem = get_object_or_404(Problem, pk=pk)
                problem_log_objs = problem.problem_log.all()
                if problem_log_objs:
                    # Replace problem object in problem log
                    update_dj_contest_info_for_replace_problem(request, problem_log_objs, new_problem_obj)
                
                problem.delete() 

        except ValidationError as e:
            print(f"{type(e).__name__}:", e)
            messages.error(request, e)
            return redirect("/admin/problems/problem/")

        except problem_exceptions.ProblemReplaceUploadException as e:
            print(f"{type(e).__name__}:", e)
            messages.error(request, str(e))
            new_problem_obj.delete()
            return redirect("/admin/problems/problem/")

        except Exception as e:
            if not messages.get_messages(request):
                messages.error(request, "題目上傳失敗！！")
                new_problem_obj.delete()

            print(f"{type(e).__name__}:", e)
            return redirect("/admin/problems/problem/")
            
        return redirect("/admin/problems/problem/")

    if request.method == "GET":
        context = {
            "opts": opts,
            "available_apps": available_apps,
        }
        return render(request, "upload_zip.html", context)

@transaction.atomic
@require_http_methods(["POST"])
def problem_upload_view(request):
    try:
        problem_id_list = json.loads(request.POST.get("problemIdHidden"))
        domserver_name = request.POST.get("domserver")
        contest_id = request.POST.get("contests")

        owner_obj = request.user
        client_obj = get_object_or_404(DomServerClient, name=domserver_name)
        server_user = DomServerUser.objects.filter(owner=request.user, server_client=client_obj).first()
        
        server_client = DomServerClientModel(
            host=client_obj.host,
            username=server_user.username,
            mask_password=server_user.mask_password,
        )
        
        contest_obj = DomServerContest.objects.filter(
            server_client=client_obj, cid=contest_id
        ).first()
        problem_crawler = create_problem_crawler(server_client)

        problem_data = {
            "problem_id_list": problem_id_list,
            "owner_obj": owner_obj,
            "client_obj": client_obj,
            "contest_obj": contest_obj,
        }

        problems_upload_info, problems_obj_data_dict = handle_problems_upload(
            request=request,
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
            raise problem_exceptions.ProblemUploadException("Error to upload Problem!!")

        for pname, pid in problems_info_dict.items():
            problems_obj_data_dict[pname].update({"web_problem_id": pid})

        create_problem_log(request=request, problems_obj_data_dict=problems_obj_data_dict)

        messages.success(request, "題目上傳成功！！")
        return redirect("/admin/problems/problem/")
    
    except problem_exceptions.ProblemUploadException as e:
        print(f"{type(e).__name__}:", e)
        from utils.problems.views import handle_upload_error_problem
        result_error_problem_name = handle_upload_error_problem(problems_obj_data_dict, problem_crawler)
        messages.error(request, f"{e} {result_error_problem_name} 已存在!!")
        return redirect("/admin/problems/problem/")
    
    except Exception as e:
        if not messages.get_messages(request):
            messages.error(request, "題目上傳錯誤！！嘗試更改壓縮檔名名稱")

        print(f"{type(e).__name__}:", e)
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
        server_user = DomServerUser.objects.filter(owner=request.user, server_client=server_object).first()
        

        server_client = DomServerClientModel(
            host=server_object.host,
            username=server_user.username,
            mask_password=server_user.mask_password,
        )
        
        upload_problem_info = upload_problem_info_process(
            queryset=queryset, server_client=server_client
        )

        if request.user.is_superuser:
            contest_queryset = DomServerContest.objects.filter(
                server_client=server_object
            )
        else:
            contest_queryset = DomServerContest.objects.filter(
                owner=request.user, server_client=server_object
            )

        contests_data_dict = {
            obj.short_name: obj.cid for obj in contest_queryset
        }

        if not request.user.is_superuser:
            demo_contest = DomServerContest.objects.filter(
                server_client=server_object, short_name="demo"
            ).first()

            contests_data = {demo_contest.short_name: demo_contest.cid}
            contests_data.update(contests_data_dict)
        else:
            contests_data = contests_data_dict

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