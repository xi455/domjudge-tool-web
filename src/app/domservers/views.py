import datetime
import json

from datetime import datetime

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from app.users.models import User
from app.problems.models import ProblemServerLog
from app.domservers import exceptions as domserver_exceptions
from app.domservers.forms import DomServerContestForm
from app.domservers.models import DomServerClient, DomServerContest

from utils import exceptions as utils_exceptions
from utils.admins import create_problem_crawler, get_contest_all_and_page_obj
from utils.views import (
    contest_problem_shortname_process,
    get_available_apps,
)
from utils.domserver.views import create_contest_record, handle_problem_log_state

# Create your views here.

def contest_format_and_upload(problem_crawler, creat_contest_data):
    """
    Formats and uploads a contest using the provided problem_crawler and create_contest_data.

    Args:
        problem_crawler: The problem crawler object used to format and upload the contest.
        create_contest_data: The data used to create the contest.

    Returns:
        The result of the contest and problem creation process.
    """
    contest_information = problem_crawler.contest_format_process(
        contest_data=creat_contest_data
    )
    contest_information.update({"contest[save]": ""})

    return problem_crawler.contest_and_problem_create(create_contest_information=contest_information)


@require_http_methods(["GET", "POST"])
def contest_create_view(request):
    available_apps = get_available_apps(request)

    if request.method == "POST":
        form = DomServerContestForm(request.POST)
        server_client_id = request.POST.get("server_client_id")

        if form.is_valid():
            creat_contest_data = form.cleaned_data
            client_obj = DomServerClient.objects.get(id=server_client_id)

            problem_crawler = create_problem_crawler(client_obj)
            problem_data_dict = problem_crawler.get_problems()
            contest_all_name = problem_crawler.get_contest_all_name()

            if form.cleaned_data["short_name"] in contest_all_name:
                messages.error(request, "考區簡稱重複！！請重新輸入")
                return redirect(f"/contest/create/?server_client_id={server_client_id}")
            
            create_response = contest_format_and_upload(problem_crawler, creat_contest_data)
            
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
                "problem_data_dict": problem_data_dict,
                "opts": client_obj._meta,
                "available_apps": available_apps,
            }

            return render(request, "contest_creat_selected_problem.html", context)

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
    create_contest_info = contest_problem_shortname_process(form_data=form_data)
    available_apps = get_available_apps(request)

    client_obj = DomServerClient.objects.get(id=id)
    problem_crawler = create_problem_crawler(client_obj)
    contest_cid = DomServerContest.objects.get(short_name=create_contest_info.get("contest[shortname]")).cid

    upload_response = problem_crawler.contest_problem_upload(contest_id=contest_cid, problem_data=create_contest_info)

    if upload_response:
        # create_contest_record(request=request, problem_crawler=problem_crawler)
        messages.success(request, "題目上傳成功！！")
    else:
        messages.error(request, "題目上傳失敗！！")

    # get all contest
    page_obj = get_contest_all_and_page_obj(
        request=request, problem_crawler=problem_crawler
    )

    context = {
        "page_obj": page_obj,
        "server_client_id": client_obj.id,
        "server_client_name": client_obj.name,
        "opts": client_obj._meta,
        "available_apps": available_apps,
    }

    return render(request, "contest_list.html", context)


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
def contest_information_edit_view(request, server_id, contest_id, cid):
    client_obj = DomServerClient.objects.get(id=server_id)
    problem_crawler = create_problem_crawler(client_obj)
    available_apps = get_available_apps(request)
    
    if request.method == "POST":
        contest_obj = get_object_or_404(DomServerContest, id=contest_id)
        form = DomServerContestForm(request.POST, instance=contest_obj)

        if form.is_valid():
            contest_update_data = form.cleaned_data

            # get the all problem
            problem_data_dict = problem_crawler.get_problems()
            contest_update_data = problem_crawler.contest_format_process(contest_data=contest_update_data)
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
            result = problem_crawler.contest_problem_upload(contest_id=cid, problem_data=contest_update_data)
            
            if result:
                messages.success(request, "考區編輯成功！！")

            context = {
                "server_client_id": client_obj.id,
                "server_client_name": client_obj.name,
                "cid": cid,
                "contest_update_data_json": contest_update_data_json,
                "existing_problem_id_list": existing_problem_id_list,
                "problem_data_dict": problem_data_dict,
                "opts": client_obj._meta,
                "available_apps": available_apps,
            }
            return render(request, "contest_edit_selected_problem.html", context)

    contest_obj = get_object_or_404(DomServerContest, id=contest_id)
    if request.method == "GET":
        form = DomServerContestForm(instance=contest_obj)

    context = {
        "server_client_id": client_obj.id,
        "server_client_name": client_obj.name,
        "contest_id": contest_id,
        "cid": cid,
        "form": form,
        "opts": client_obj._meta,
        "available_apps": available_apps,
    }

    return render(request, "contest_edit.html", context)


@require_http_methods(["POST"])
def contest_problem_shortname_edit_view(request, id, cid):
    form_data = request.POST
    client_obj = DomServerClient.objects.get(id=id)
    problem_crawler = create_problem_crawler(client_obj)
    available_apps = get_available_apps(request)

    # Get the latest contest area information
    contest_info = contest_problem_shortname_process(form_data=form_data)

    handle_problem_log_state(request, cid, client_obj, "移除", problem_crawler)
    # Delete the problem information in the old contest area
    old_problem_info_remove_process(problem_crawler=problem_crawler, cid=cid)

    # Update contest information
    upload_response = problem_crawler.contest_problem_upload(
        contest_id=cid, problem_data=contest_info
    )

    if upload_response:
        handle_problem_log_state(request, cid, client_obj, "新增", problem_crawler)
        messages.success(request, "考區編輯成功！！")
    else:
        messages.error(request, "考區編輯失敗！！")

    # get all contest
    page_obj = get_contest_all_and_page_obj(
        request=request, problem_crawler=problem_crawler
    )

    context = {
        "page_obj": page_obj,
        "server_client_id": client_obj.id,
        "server_client_name": client_obj.name,
        "opts": client_obj._meta,
        "available_apps": available_apps,
    }

    return render(request, "contest_list.html", context)


def old_problem_info_remove_process(problem_crawler, cid):

    # The old competition question information will be deleted
    # (applicable to competition information changes)

    try:
        old_problem_information = problem_crawler.get_contest_or_problem_information(
            contest_id=cid, need_content="problem"
        )

        problem_need_delete = old_problem_information

        if problem_need_delete:
            problem_need_delete_id = [
                value
                for key, value in problem_need_delete.items()
                if "[problem]" in key
            ]

            for problem_id in problem_need_delete_id:
                problem_crawler.delete_contest_problem(
                    contest_id=cid, web_problem_id=problem_id
                )

    except:
        raise utils_exceptions.CrawlerRemoveContestOldProblemsException("移除舊題目資訊時發現錯誤")


def contest_problem_selected_shortname_process(old_problem_info_dict, selected_problem):
    """
    Return the id, name, shortname information of the problem
    example: [{'name': 'Hello World', 'id': '1', 'shortname': 'Hello World test'}]
    return dict format problem_id: problem_shortname
    """

    old_problem_info_keys = old_problem_info_dict.keys()
    for data in selected_problem:
        if data["id"] in old_problem_info_keys:
            data["shortname"] = old_problem_info_dict[data.get("id")]
        else:
            data["shortname"] = data.get("name")

    return selected_problem


def contest_problem_information_update_process(
    problem_information, old_problem_information, selected_problem
):
    """
    Get the shortname of the old problem information
    Replace the shortname of the current problem information
    Reture problem information and selected_problem

    old_problem_info_dict example: {'3': 'test'}
    old_problem_info_dict format problem_id: problem_shortname
    """

    old_problem_info_dict = dict()
    for key, value in old_problem_information.items():
        if key[21:-1] == "problem":
            problem_shortname = f"contest[problems][{key[18:19]}][shortname]"
            old_problem_info_dict[value] = old_problem_information[problem_shortname]

    for key, value in problem_information.items():
        if key[21:-1] == "problem" and value in old_problem_info_dict.keys():
            problem_shortname = f"contest[problems][{key[18:19]}][shortname]"
            problem_information[problem_shortname] = old_problem_info_dict[value]

    # Get the old shortname information in the contest area problem
    selected_problem = contest_problem_selected_shortname_process(
        old_problem_info_dict=old_problem_info_dict, selected_problem=selected_problem
    )

    return problem_information, selected_problem


@require_http_methods(["POST"])
def contest_select_problem_edit_view(request, id, cid):

    available_apps = get_available_apps(request)

    # Extract contest data and selected problems from the request
    contest_information = json.loads(request.POST.get("contestDataJson"))
    selected_problem = json.loads(request.POST.get("selectedCheckboxes"))

    client_obj = DomServerClient.objects.get(id=id)
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


def contest_problem_copy_view(request, id, cid):
    """
    Copy a contest problem.

    Args:
        request: The HTTP request object.
        id: The ID of the DomServerClient.
        cid: The ID of the contest.

    Returns:
        The rendered contest_list.html template with the necessary context.
    """
    try:
        client_obj = DomServerClient.objects.get(id=id)
        problem_crawler = create_problem_crawler(client_obj)
        available_apps = get_available_apps(request)

        # Get now time
        current_time = datetime.now()
        format_time = current_time.strftime("%Y%m%d%H%M%S")

        # Get contest information
        contest_problem_information_dict = (
            problem_crawler.get_contest_or_problem_information(contest_id=cid)
        )

        # Renameing of contest
        contest_problem_information_dict[
            "contest[shortname]"
        ] = f"{contest_problem_information_dict['contest[shortname]']}_copy_{format_time}"

        # Create a new contest area
        problem_crawler.contest_and_problem_create(
            create_contest_information=contest_problem_information_dict
        )

        # Create a new contest record
        create_contest_record(
            request=request,
            problem_crawler=problem_crawler,
            contest_shortname=contest_problem_information_dict["contest[shortname]"],
            server_client_id=id,
        )

        # Get all contest
        page_obj = get_contest_all_and_page_obj(
            request=request, problem_crawler=problem_crawler
        )

        context = {
            "page_obj": page_obj,
            "server_client_id": client_obj.id,
            "server_client_name": client_obj.name,
            "opts": client_obj._meta,
            "available_apps": available_apps,
        }

        return render(request, "contest_list.html", context)
    except Exception:
        raise domserver_exceptions.ContestCopyException(
            "Errors in copying the Contest area."
        )
