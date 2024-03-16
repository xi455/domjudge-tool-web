import json

from django.db import transaction
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from app.users.models import User
from app.problems.models import ProblemServerLog
from app.domservers.forms import DomServerContestForm
from app.domservers.models import DomServerClient, DomServerContest

from app.domservers.views.validator import validator_problem_exist, check_create_problem_log_for_contest_edit
from app.domservers.views.contest import filter_contest_selected_problem, create_copy_contest_record, get_copy_problem_log_and_upload_process
from app.domservers.views.shortname import contest_problem_information_update_process, rename_shortname_and_handle_contest_copy_and_upload, contest_problem_shortname_process

from utils.admins import create_problem_crawler
from utils.domserver.views import create_contest_record, update_problem_log_state, handle_problem_log, old_problem_info_remove_process
from utils.views import get_available_apps
# Create your views here.


@require_http_methods(["GET", "POST"])
def contest_create_view(request):
    available_apps = get_available_apps(request)

    if request.method == "POST":
        try:
            form = DomServerContestForm(request.POST)
            server_client_id = request.POST.get("server_client_id")

            if form.is_valid():
                creat_contest_data = form.cleaned_data
                client_obj = DomServerClient.objects.get(id=server_client_id)

                problem_crawler = create_problem_crawler(client_obj)

                if DomServerContest.objects.filter(server_client=client_obj, short_name=form.cleaned_data["short_name"]).exists():
                    messages.error(request, "考區簡稱重複！！請重新輸入")
                    return redirect(f"/contest/create/?server_client_id={server_client_id}")
                
                problem_log_objs_list = filter_contest_selected_problem(request, client_obj)

                create_response = problem_crawler.contest_format_process(
                    contest_data=creat_contest_data
                )
                problem_crawler.contest_and_problem_create(
                    create_contest_information=create_response
                )

                if create_response:
                    create_contest_record(request, form, client_obj, problem_crawler)
                    messages.success(request, "考區創建成功！！")
                else:
                    messages.error(request, "考區創建失敗！！")
                    return redirect(f"/contest/create/?server_client_id={server_client_id}")

                contest_data_json = json.dumps(creat_contest_data)
                context = {
                    "server_client_id": server_client_id,
                    "server_client_name": client_obj.name,
                    "contest_data_json": contest_data_json,
                    "problem_log_objs_list": problem_log_objs_list,
                    "opts": client_obj._meta,
                    "available_apps": available_apps,
                }

                return render(request, "contest_creat_selected_problem.html", context)
            
        except Exception as e:
            print(f"{type(e).__name__}:", e)
            return redirect("/admin/domservers/domserverclient/")

    if request.method == "GET":
        initial_data = {
            "short_name": "contest",
            "name": "new contest",
            "activate_time": "2024-01-01 12:00:00 Asia/Taipei",  # 必須得晚於 start_time
            "start_time": "2024-01-01 13:00:00 Asia/Taipei",
            "scoreboard_freeze_length": "2024-01-01 15:00:00 Asia/Taipei",  # 時間得在 start - end 之間
            "end_time": "2024-01-01 18:00:00 Asia/Taipei",
            "scoreboard_unfreeze_time": "2024-01-01 20:00:00 Asia/Taipei",  # 解凍時間必須大於結束時間
            "deactivate_time": "2024-01-01 22:00:00 Asia/Taipei",  # 停用時間必須大於解凍時間
        }

        form = DomServerContestForm(initial=initial_data)
        server_client_id = request.GET.get("server_client_id")
        obj = DomServerClient.objects.get(id=server_client_id)

    context = {
        "form": form,
        "server_client_id": server_client_id,
        "server_client_name": obj.name,
        "opts": obj._meta,
        "available_apps": available_apps,
    }

    return render(request, "contest_create.html", context)

@require_http_methods(["POST"])
def contest_problem_upload_view(request, id):
    form_data = request.POST
    client_obj = DomServerClient.objects.get(id=id)

    try:
        create_contest_info = contest_problem_shortname_process(request=request, form_data=form_data)

        problem_crawler = create_problem_crawler(client_obj)
        contest_obj = DomServerContest.objects.get(
            short_name=create_contest_info.get("contest[shortname]")
        )
        contest_cid = contest_obj.cid

        upload_response = problem_crawler.contest_problem_upload(
            contest_id=contest_cid, problem_data=create_contest_info
        )

        if upload_response:
            messages.success(request, "題目上傳成功！！")
            handle_problem_log(form_data, request, client_obj, contest_obj)
        else:
            messages.error(request, "題目上傳失敗！！")

        return redirect("admin:contest-items", obj_id=client_obj.id)
    except Exception as e:
        print(f"{type(e).__name__}:", e)
        return redirect("admin:contest-items", obj_id=client_obj.id)


@require_http_methods(["POST"])
def contest_problem_shortname_create_view(request):
    available_apps = get_available_apps(request)
    server_client_id = request.POST.get("server_client_id")
    contest_data = json.loads(request.POST.get("contestDataJson"))
    selected_problem_dict = json.loads(request.POST.get("selectedCheckboxes"))

    client_obj = DomServerClient.objects.get(id=server_client_id)
    problem_crawler = create_problem_crawler(client_obj)

    contest_information = problem_crawler.contest_format_process(
        contest_data=contest_data
    )

    problem_information = problem_crawler.problem_format_process(
        problem_data=selected_problem_dict
    )

    contest_information.update(problem_information)
    contest_information.update({"contest[save]": ""})
    create_information = contest_information

    create_data_json = json.dumps(create_information)

    context = {
        "server_client_id": server_client_id,
        "server_client_name": client_obj.name,
        "create_data_json": create_data_json,
        "selected_problem_dict": selected_problem_dict,
        "opts": client_obj._meta,
        "available_apps": available_apps,
    }

    return render(request, "contest_problem_shortname_create.html", context)


@require_http_methods(["GET", "POST"])
def contest_information_edit_view(request, server_id, contest_id, cid, page_number):
    client_obj = DomServerClient.objects.get(id=server_id)
    problem_crawler = create_problem_crawler(client_obj)
    available_apps = get_available_apps(request)

    if request.method == "POST":
        contest_obj = get_object_or_404(DomServerContest, id=contest_id)
        form = DomServerContestForm(request.POST, instance=contest_obj)

        if form.is_valid():
            contest_update_data = form.cleaned_data

            # get the selected problem
            problem_log_objs_list = filter_contest_selected_problem(request, client_obj)
            
            # handle contest format
            contest_update_data = problem_crawler.contest_format_process(
                contest_data=contest_update_data
            )
            contest_update_data_json = json.dumps(contest_update_data)

            # get the existing problem
            existing_problem_informtion_dict = (
                problem_crawler.get_contest_or_problem_information(
                    contest_id=cid, need_content="problem"
                )
            )
            existing_problem_id_list = [
                value
                for key, value in existing_problem_informtion_dict.items()
                if "[problem]" in key
            ]

            form.save()
            contest_update_data.update(existing_problem_informtion_dict)
            contest_update_data.update({"contest[save]": ""})
            result = problem_crawler.contest_problem_upload(
                contest_id=cid, problem_data=contest_update_data
            )

            if result:
                messages.success(request, "考區編輯成功！！")

            context = {
                "server_client_id": client_obj.id,
                "server_client_name": client_obj.name,
                "cid": cid,
                "contest_update_data_json": contest_update_data_json,
                "existing_problem_id_list": existing_problem_id_list,
                "problem_log_objs_list": problem_log_objs_list,
                "opts": client_obj._meta,
                "available_apps": available_apps,
            }
            return render(request, "contest_edit_selected_problem.html", context)

    contest_obj = get_object_or_404(DomServerContest, id=contest_id)
    if request.method == "GET":
        form = DomServerContestForm(instance=contest_obj)

    request.session["page_number"] = page_number
    context = {
        "server_client_id": client_obj.id,
        "server_client_name": client_obj.name,
        "contest_id": contest_id,
        "cid": cid,
        "form": form,
        "page_number": page_number,
        "opts": client_obj._meta,
        "available_apps": available_apps,
    }

    return render(request, "contest_edit.html", context)


@transaction.atomic
@require_http_methods(["POST"])
def contest_problem_shortname_edit_view(request, id, cid):
    form_data = request.POST
    client_obj = DomServerClient.objects.get(id=id)
    problem_crawler = create_problem_crawler(client_obj)

    try:
        # Get the latest contest area information
        contest_info = contest_problem_shortname_process(request=request, form_data=form_data)
        contest_obj = DomServerContest.objects.get(
            server_client=client_obj, short_name=contest_info.get("contest[shortname]")
        )
        
        # Delete the problem information in the old contest area
        update_problem_log_state(request, "移除", client_obj, contest_obj)
        old_problem_info_remove_process(request=request, problem_crawler=problem_crawler, cid=cid)

        # Update contest information
        upload_response = problem_crawler.contest_problem_upload(
            contest_id=cid, problem_data=contest_info
        )

        if upload_response:
            problem_exist_valid_result = validator_problem_exist(contest_info)
            
            if problem_exist_valid_result:
                update_problem_log_state(request, "新增", client_obj, contest_obj)

            check_create_problem_log_for_contest_edit(request, client_obj, contest_obj, form_data, problem_crawler, cid)
            
            messages.success(request, "考區編輯成功！！")
        else:
            messages.error(request, "考區編輯失敗！！")

        return redirect('admin:contest-items', obj_id=client_obj.id)

    except Exception as e:
        print(f"{type(e).__name__}:", e)
        return redirect("admin:contest-items", obj_id=client_obj.id)


@require_http_methods(["POST"])
def contest_select_problem_edit_view(request, id, cid):

    available_apps = get_available_apps(request)

    # Extract contest data and selected problems from the request
    contest_information = json.loads(request.POST.get("contestDataJson"))
    selected_problem = json.loads(request.POST.get("selectedProblem"))

    client_obj = DomServerClient.objects.get(id=id)

    try:
        problem_crawler = create_problem_crawler(client_obj)

        # Get problem information format
        problem_information = problem_crawler.problem_format_process(
            problem_data=selected_problem
        )

        # Get old problem information format
        old_problem_information = problem_crawler.get_contest_or_problem_information(
            contest_id=cid, need_content="problem"
        )

        # Add old problem information to new problem
        problem_information, selected_problem = contest_problem_information_update_process(
            request=request,
            problem_information=problem_information,
            old_problem_information=old_problem_information,
            selected_problem=selected_problem,
        )

        # Sum the competition and problem data and convert them into json
        contest_information.update(problem_information)
        contest_information.update({"contest[save]": ""})
        create_information = contest_information

        create_data_json = json.dumps(create_information)

        context = {
            "cid": cid,
            "server_client_id": client_obj.id,
            "server_client_name": client_obj.name,
            "selected_problem_dict": selected_problem,
            "create_data_json": create_data_json,
            "opts": client_obj._meta,
            "available_apps": available_apps,
        }

        return render(request, "contest_problem_shortname_edit.html", context)
    
    except Exception as e:
        print(f"{type(e).__name__}:", e)
        return redirect("contest_select_problem_edit", id=id, cid=cid)


@transaction.atomic
def contest_copy_view(request, id, contest_id, cid):
    """
    Copy a contest problem.

    Args:
        request (HttpRequest): The HTTP request object.
        id (int): The ID of the DomServerClient object.
        contest_id (int): The ID of the DomServerContest object.
        cid (str): Contest Area ID on the website.

    Returns:
        HttpResponse: The HTTP response object containing the rendered contest list page.

    Raises:
        ContestCopyException: If there are errors in copying the contest area.
    """
    client_obj = DomServerClient.objects.get(id=id)
    problem_crawler = create_problem_crawler(client_obj)

    try:
        # Rename the contest shortname and upload the contest
        contest_shortname_rename = rename_shortname_and_handle_contest_copy_and_upload(request, problem_crawler, cid)

        # Create a new contest area record
        contest_obj = DomServerContest.objects.get(id=contest_id)
        new_contest_obj = create_copy_contest_record(contest_shortname_rename, contest_obj, problem_crawler)

        # Get the problem information and upload it for processing
        problem_logs = ProblemServerLog.objects.filter(
            server_client=client_obj,
            contest=contest_obj,
        ).order_by("-id")

        get_copy_problem_log_and_upload_process(request, problem_logs, client_obj, new_contest_obj)

        return redirect("admin:contest-items", obj_id=client_obj.id)
    
    except Exception as e:
        print(f"{type(e).__name__}:", e)
        return redirect("admin:contest-items", obj_id=client_obj.id)
