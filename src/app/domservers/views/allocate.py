import json

from django.contrib import messages
from django.db import transaction, IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from app.problems.models import ProblemServerLog
from app.domservers.forms import DomServerContestForm
from app.domservers.models import DomServerUser, DomServerContest

from app.domservers.views.validator import validator_problem_exist, check_create_problem_log_for_contest_edit
from app.domservers.views.contest import filter_contest_selected_problem, create_copy_contest_record, get_copy_problem_log_and_upload_process
from app.domservers.views.shortname import contest_problem_information_update_process, rename_shortname_and_handle_contest_copy_and_upload, contest_problem_shortname_process

from app.domservers import exceptions as domserver_exceptions
from app.problems import exceptions as problem_exceptions

from utils.validator_pydantic import DomServerClientModel
from utils.admins import create_problem_crawler
from utils.domserver.views import form_create_contest_record, update_problem_log_state, handle_problem_log, old_problem_info_remove_process
from utils.views import get_available_apps
# Create your views here.


@transaction.atomic
@require_http_methods(["GET", "POST"])
def contest_create_view(request):
    available_apps = get_available_apps(request)

    if request.method == "POST":
        try:
            form = DomServerContestForm(request.POST)
            server_user_id = request.POST.get("server_user_id")

            if form.is_valid():
                creat_contest_data = form.cleaned_data
                server_user = DomServerUser.objects.get(id=server_user_id)
                client_obj = server_user.server_client

                server_client = DomServerClientModel(
                    host=client_obj.host,
                    username=server_user.username,
                    mask_password=server_user.mask_password,
                )
                
                problem_crawler = create_problem_crawler(server_client)

                if DomServerContest.objects.filter(server_client=client_obj, short_name=form.cleaned_data["short_name"]).exists():
                    messages.error(request, "考區簡稱重複！！請重新輸入")
                    raise domserver_exceptions.ContestCreateDuplicateException("Contest Shortname Duplicate!!")
                
                problem_log_objs_list = filter_contest_selected_problem(request, client_obj)

                create_response = problem_crawler.contest_format_process(
                    contest_data=creat_contest_data
                )
                problem_crawler.contest_and_problem_create(
                    create_contest_information=create_response
                )

                if create_response:
                    form_create_contest_record(request, form, client_obj, problem_crawler)
                    messages.success(request, "考區創建成功！！")
                else:
                    messages.error(request, "考區創建失敗！！")
                    raise domserver_exceptions.ContestCreateException("考區創建失敗！！")

                contest_data_json = json.dumps(creat_contest_data)
                context = {
                    "server_user": server_user,
                    "client_obj": client_obj,
                    "contest_data_json": contest_data_json,
                    "problem_log_objs_list": problem_log_objs_list,
                    "opts": client_obj._meta,
                    "available_apps": available_apps,
                }

                return render(request, "contest_creat_selected_problem.html", context)

        except domserver_exceptions.ContestCreateDuplicateException as e:
            print(f"{type(e).__name__}:", e)
        except Exception as e:
            print(f"{type(e).__name__}:", e)

        return redirect(f"/domserver/contest/create/?server_user_id={server_user.id}")

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

    server_user_id = request.GET.get("server_user_id")
    server_user = DomServerUser.objects.get(id=server_user_id)
    server_client = server_user.server_client

    context = {
        "server_user": server_user,
        "form": form,
        "server_client_name": server_client.name,
        "opts": server_client._meta,
        "available_apps": available_apps,
    }

    return render(request, "contest_create.html", context)


@transaction.atomic
@require_http_methods(["POST"])
def contest_problem_info_upload_view(request, server_user_id):
    form_data = request.POST
    server_user = DomServerUser.objects.get(id=server_user_id)
    client_obj = server_user.server_client
    server_client = DomServerClientModel(
        host=client_obj.host,
        username=server_user.username,
        mask_password=server_user.mask_password,
    )

    try:
        create_contest_info = contest_problem_shortname_process(request=request, form_data=form_data)

        problem_crawler = create_problem_crawler(server_client)
        contest_obj = DomServerContest.objects.get(
            short_name=create_contest_info.get("contest[shortname]")
        )
        contest_cid = contest_obj.cid

        upload_result = problem_crawler.contest_problem_upload(
            contest_id=contest_cid, problem_data=create_contest_info
        )

        if upload_result:
            messages.success(request, "題目上傳成功！！")
            handle_problem_log(request, form_data, server_client, client_obj, contest_obj)
        else:
            messages.error(request, "題目上傳失敗！！")
            raise problem_exceptions.ProblemUploadException("Error to upload Problem!!")

        return redirect("admin:contest-items", obj_id=server_user.id)
    except Exception as e:
        print(f"{type(e).__name__}:", e)
        return redirect("admin:contest-items", obj_id=server_user.id)


@require_http_methods(["POST"])
def contest_problem_shortname_create_view(request):
    available_apps = get_available_apps(request)
    server_user_id = request.POST.get("server_user_id")
    contest_data = json.loads(request.POST.get("contestDataJson"))
    selected_problem_dict = json.loads(request.POST.get("selectedCheckboxes"))

    server_user = DomServerUser.objects.get(id=server_user_id)
    client_obj = server_user.server_client
    server_client = DomServerClientModel(
        host=client_obj.host,
        username=server_user.username,
        mask_password=server_user.mask_password,
    )

    problem_crawler = create_problem_crawler(server_client)

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
        "server_user": server_user,
        "create_data_json": create_data_json,
        "selected_problem_dict": selected_problem_dict,
        "opts": server_user._meta,
        "available_apps": available_apps,
    }

    return render(request, "contest_problem_shortname_create.html", context)


@transaction.atomic
@require_http_methods(["GET", "POST"])
def contest_information_edit_view(request, server_user_id, contest_id, cid, page_number):
    server_user = DomServerUser.objects.get(id=server_user_id)
    client_obj = server_user.server_client

    server_client = DomServerClientModel(
        host=client_obj.host,
        username=server_user.username,
        mask_password=server_user.mask_password,
    )

    problem_crawler = create_problem_crawler(server_client)
    available_apps = get_available_apps(request)

    try:
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

                existing_problem_log_info = ProblemServerLog.objects.filter(
                    server_client=client_obj,
                    contest=contest_obj,
                    web_problem_state="新增",
                ).order_by("-id")

                existing_problem_id_list = [
                    problem.web_problem_id for problem in existing_problem_log_info
                ]
                
                # get the existing problem for the contest area in Domjudge web
                existing_problem_informtion_dict = (
                    problem_crawler.get_contest_or_problem_information(
                        contest_id=cid, need_content="problem"
                    )
                )

                form.save()
                contest_update_data.update(existing_problem_informtion_dict)
                contest_update_data.update({"contest[save]": ""})
                result = problem_crawler.contest_problem_upload(
                    contest_id=cid, problem_data=contest_update_data
                )

                if result:
                    messages.success(request, "考區編輯成功！！")
                else:
                    messages.error(request, "考區編輯失敗！！")
                    raise domserver_exceptions.ContestUpdateException("Contest Area Edit Error!!")

                context = {
                    "server_user": server_user,
                    "cid": cid,
                    "contest_update_data_json": contest_update_data_json,
                    "existing_problem_id_list": existing_problem_id_list,
                    "problem_log_objs_list": problem_log_objs_list,
                    "opts": server_user._meta,
                    "available_apps": available_apps,
                }
                return render(request, "contest_edit_selected_problem.html", context)
    
    except IntegrityError as e:
        print(f"{type(e).__name__}:", e)
        return redirect("domservers:contest_information_edit", server_user=server_user.id, contest_id=contest_id, cid=cid, page_number=page_number)
    
    contest_obj = get_object_or_404(DomServerContest, id=contest_id)
    if request.method == "GET":
        form = DomServerContestForm(instance=contest_obj)

    request.session["page_number"] = page_number
    context = {
        "server_user": server_user,
        "contest_id": contest_id,
        "cid": cid,
        "form": form,
        "page_number": page_number,
        "opts": server_user._meta,
        "available_apps": available_apps,
    }

    return render(request, "contest_edit.html", context)


@transaction.atomic
@require_http_methods(["POST"])
def contest_problem_shortname_edit_view(request, server_user_id, cid):
    form_data = request.POST
    server_user = DomServerUser.objects.get(id=server_user_id)
    client_obj = server_user.server_client
    server_client = DomServerClientModel(
        host=client_obj.host,
        username=server_user.username,
        mask_password=server_user.mask_password,
    )

    problem_crawler = create_problem_crawler(server_client)

    try:
        # Get the latest contest area information
        contest_info = contest_problem_shortname_process(request=request, form_data=form_data)
        
        contest_obj = DomServerContest.objects.get(
            server_client=client_obj, short_name=contest_info.get("contest[shortname]")
        )

        # Delete the problem information in the old contest area
        problem_need_delete_id = old_problem_info_remove_process(request=request, problem_crawler=problem_crawler, cid=cid)

        # Update the problem log state
        problem_log = update_problem_log_state("移除", server_client, client_obj, contest_obj)
        ProblemServerLog.objects.bulk_update(problem_log, ["web_problem_state"])

        # Update contest information
        upload_response = problem_crawler.contest_problem_upload(
            contest_id=cid, problem_data=contest_info
        )

        if upload_response:
            problem_exist_valid_result = validator_problem_exist(contest_info)
            
            if problem_exist_valid_result:
                problem_log = update_problem_log_state("新增", server_client, client_obj, contest_obj)

            check_create_problem_log_for_contest_edit(request, server_client, client_obj, contest_obj, form_data, problem_crawler, cid)
            
            messages.success(request, "考區編輯成功！！")
            ProblemServerLog.objects.bulk_update(problem_log, ["web_problem_state"])
        else:
            messages.error(request, "考區編輯失敗！！")
            raise domserver_exceptions.ContestUpdateException("Contest Area Edit Error!!")

        return redirect('admin:contest-items', obj_id=server_user.id)

    except domserver_exceptions.ContestUpdateException as e:
        if problem_log:
            for log in problem_log:
                if log.web_problem_id in problem_need_delete_id:
                    log.web_problem_state = "新增"
            ProblemServerLog.objects.bulk_update(problem_log, ["web_problem_state"])

        print(f"{type(e).__name__}:", e)
        return redirect("admin:contest-items", obj_id=server_user.id)
    except Exception as e:
        print(f"{type(e).__name__}:", e)
        return redirect("admin:contest-items", obj_id=server_user.id)


@require_http_methods(["POST"])
def contest_select_problem_edit_view(request, server_user_id, cid):

    available_apps = get_available_apps(request)

    # Extract contest data and selected problems from the request
    contest_information = json.loads(request.POST.get("contestDataJson"))
    selected_problem = json.loads(request.POST.get("selectedProblem"))

    server_user = DomServerUser.objects.get(id=server_user_id)
    server_client = DomServerClientModel(
        host=server_user.server_client.host,
        username=server_user.username,
        mask_password=server_user.mask_password,
    )

    try:
        problem_crawler = create_problem_crawler(server_client)

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
            "server_user": server_user,
            "selected_problem_dict": selected_problem,
            "create_data_json": create_data_json,
            "opts": server_user._meta,
            "available_apps": available_apps,
        }

        return render(request, "contest_problem_shortname_edit.html", context)
    
    except Exception as e:
        print(f"{type(e).__name__}:", e)
        return redirect("domservers:contest_select_problem_edit", server_user.id, cid)


@transaction.atomic
def contest_copy_view(request, server_user_id, contest_id, cid):
    """
    Copy a contest problem.

    Args:
        request (HttpRequest): The HTTP request object.
        contest_id (int): The ID of the DomServerContest object.
        cid (str): Contest Area ID on the website.

    Returns:
        HttpResponse: The HTTP response object containing the rendered contest list page.

    Raises:
        ContestCopyException: If there are errors in copying the contest area.
    """

    server_user = DomServerUser.objects.get(id=server_user_id)
    client_obj = server_user.server_client
    server_client = DomServerClientModel(
        host=client_obj.host,
        username=server_user.username,
        mask_password=server_user.mask_password,
    )
    problem_crawler = create_problem_crawler(server_client)

    try:
        # Rename the contest shortname and upload the contest
        contest_shortname_rename = rename_shortname_and_handle_contest_copy_and_upload(request, problem_crawler, cid)

        # Create a new contest area record
        contest_obj = DomServerContest.objects.get(id=contest_id)
        new_contest_obj = create_copy_contest_record(request, contest_shortname_rename, contest_obj, problem_crawler)

        # Get the problem information and upload it for processing
        problem_logs = ProblemServerLog.objects.filter(
            server_client=client_obj,
            contest=contest_obj,
        ).order_by("-id")

        get_copy_problem_log_and_upload_process(request, server_client, problem_logs, client_obj, new_contest_obj)

        return redirect("admin:contest-items", obj_id=server_user.id)
    
    except Exception as e:
        print(f"{type(e).__name__}:", e)
        return redirect("admin:contest-items", obj_id=server_user.id)
