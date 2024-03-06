import datetime
import json

from datetime import datetime

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from app.domservers import exceptions as domserver_exceptions
from app.domservers.forms import DomServerContestForm
from app.domservers.models import DomServerClient, DomServerContest
from app.problems.models import ProblemServerLog
from app.users.models import User
from utils import exceptions as utils_exceptions
from utils.admins import create_problem_crawler, get_contest_all_and_page_obj
from utils.domserver.views import create_contest_record, update_problem_log_state, create_problem_log_format_and_record, handle_problem_log, get_problem_log_web_id_list
from utils.views import contest_problem_shortname_process, get_available_apps, get_contest_selected_problem_local_id
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

    return problem_crawler.contest_and_problem_create(
        create_contest_information=contest_information
    )

def filter_contest_selected_problem(request, client_obj):
    """
    Filter the contest's selected problems for a specific server client.

    Args:
        request (HttpRequest): The HTTP request object.
        client_obj (Client): The client object.

    Returns:
        list: A list of ProblemServerLog objects return the filtered contest's selected problems.
    """
    owner = User.objects.get(username=request.user.username)

    if owner.is_superuser:
        problem_objs = ProblemServerLog.objects.filter(server_client=client_obj)
    else:
        problem_objs = ProblemServerLog.objects.filter(
            owner=owner, server_client=client_obj
        )

    problem_objs_id_list = list()
    problem_log_objs_list = list()
    for problem in problem_objs:
        if problem.problem.id not in problem_objs_id_list:
            problem_objs_id_list.append(problem.problem.id)
            problem_log_objs_list.append(problem)

    return problem_log_objs_list

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
            
            contest_all_name = problem_crawler.get_contest_all_name()

            if form.cleaned_data["short_name"] in contest_all_name:
                messages.error(request, "考區簡稱重複！！請重新輸入")
                return redirect(f"/contest/create/?server_client_id={server_client_id}")
            
            problem_log_objs_list = filter_contest_selected_problem(request, client_obj)

            create_response = contest_format_and_upload(
                problem_crawler, creat_contest_data
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

    # get all contest
    page_obj = get_contest_all_and_page_obj(request=request, client_obj=client_obj)

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


def validator_problem_exist(contest_info):
    """
    Validate if the problem information exists in the contest information.

    Args:
        contest_info (dict): The contest information.

    Returns:
        bool: True if the problem information exists in the contest information; otherwise, False.
    """
    for key in contest_info:
        if "problems" in key:
            return True

    return False


def check_create_problem_log_for_contest_edit(request, client_obj, contest_obj, form_data, problem_crawler, cid):
    """
    Check if problem logs need to be created for contest edit.

    Args:
        request: The HTTP request object.
        client_obj: The client object.
        contest_obj: The contest object.
        form_data: The form data.
        problem_crawler: The problem crawler object.
        cid: The contest ID.

    Returns:
        None
    """
    problem_log_web_id_set = {_ for _ in get_problem_log_web_id_list(cid, problem_crawler)}
    problem_logs_object = ProblemServerLog.objects.filter(
        server_client=client_obj,
        contest=contest_obj,
        web_problem_id__in=problem_log_web_id_set
    )

    if problem_logs_object.count() < len(problem_log_web_id_set):
        create_problem_log_for_contest_edit(request, client_obj, contest_obj, form_data, problem_log_web_id_set, problem_logs_object)

def create_problem_log_for_contest_edit(request, client_obj, contest_obj, form_data, problem_log_web_id_set, problem_logs_object):
    """
    Create problem logs for contest edit.

    Args:
        request: The request object.
        client_obj: The client object.
        contest_obj: The contest object.
        form_data: The form data.
        problem_log_web_id_set: The set of problem log web IDs.
        problem_logs_object: The problem logs object.

    Returns:
        None
    """
    existing_problem_id_set = {obj.web_problem_id for obj in problem_logs_object if obj.web_problem_id in problem_log_web_id_set}
    no_existing_problem_id_set = problem_log_web_id_set - existing_problem_id_set

    problem_info_dict = get_contest_selected_problem_local_id(form_data)
    problem_local_id_dict = {web_id:problem_info_dict.get(web_id) for web_id in no_existing_problem_id_set}

    problem_objs_dict = problem_local_id_dict
    if problem_objs_dict:
        create_problem_log_format_and_record(
            request, client_obj, contest_obj, problem_objs_dict, no_existing_problem_id_set=no_existing_problem_id_set
        )

@require_http_methods(["POST"])
def contest_problem_shortname_edit_view(request, id, cid):
    form_data = request.POST
    client_obj = DomServerClient.objects.get(id=id)
    problem_crawler = create_problem_crawler(client_obj)
    available_apps = get_available_apps(request)

    # Get the latest contest area information
    contest_info = contest_problem_shortname_process(form_data=form_data)
    contest_obj = DomServerContest.objects.get(
        server_client=client_obj, short_name=contest_info.get("contest[shortname]")
    )
    
    # Delete the problem information in the old contest area
    update_problem_log_state(request, "移除", client_obj, contest_obj)
    old_problem_info_remove_process(problem_crawler=problem_crawler, cid=cid)

    # Update contest information
    upload_response = problem_crawler.contest_problem_upload(
        contest_id=cid, problem_data=contest_info
    )

    if upload_response:
        problem_exist_valid_result = validator_problem_exist(contest_info)
        
        if problem_exist_valid_result:
            update_problem_log_state(request, "新增", client_obj, contest_obj)

        check_create_problem_log_for_contest_edit(request, client_obj, contest_obj, form_data, problem_crawler, cid)
        
        # test ----------------
        messages.success(request, "考區編輯成功！！")
    else:
        messages.error(request, "考區編輯失敗！！")

    # get all contest
    page_obj = get_contest_all_and_page_obj(request=request, client_obj=client_obj)

    context = {
        "page_obj": page_obj,
        "server_client_id": client_obj.id,
        "server_client_name": client_obj.name,
        "opts": client_obj._meta,
        "available_apps": available_apps,
    }

    return render(request, "contest_list.html", context)


def old_problem_info_remove_process(problem_crawler, cid):
    """
    Remove old problem information from the contest.

    Args:
        problem_crawler (ProblemCrawler): The problem crawler object.
        cid (str): The contest ID.

    Raises:
        CrawlerRemoveContestOldProblemsException: If an error occurs while removing old problem information.

    """
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
    selected_problem = json.loads(request.POST.get("selectedProblem"))

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


def rename_shortname_and_handle_contest_copy_and_upload(problem_crawler, cid):
    # Get now time
    current_time = datetime.now()
    format_time = current_time.strftime("%Y%m%d%H%M%S")

    # Get contest information
    contest_problem_information_dict = (
        problem_crawler.get_contest_or_problem_information(contest_id=cid)
    )

    # Renameing of contest shortname
    contest_shortname_rename = f"{contest_problem_information_dict['contest[shortname]']}_copy_{format_time}"
    contest_problem_information_dict["contest[shortname]"] = contest_shortname_rename

    # Create a new contest area
    problem_crawler.contest_and_problem_create(
        create_contest_information=contest_problem_information_dict
    )

    return contest_shortname_rename

def create_copy_contest_record(contest_shortname_rename, contest_obj, problem_crawler):
    """
    Create a copy of a contest record with the given contest shortname rename.

    Args:
        contest_shortname_rename (str): The new shortname for the copied contest.
        contest_obj (DomServerContest): The original contest object to be copied.
        problem_crawler (ProblemCrawler): The problem crawler object.

    Returns:
        DomServerContest: The newly created contest object.
    """
    # Get the new contest area id
    cid = problem_crawler.get_contest_name_cid(contest_shortname_rename)

    new_contest_obj = DomServerContest.objects.create(
        owner=contest_obj.owner,
        server_client=contest_obj.server_client,
        cid=cid,
        name=contest_obj.name,
        short_name=contest_shortname_rename,
        start_time=contest_obj.start_time,
        end_time=contest_obj.end_time,
        activate_time=contest_obj.activate_time,
        scoreboard_freeze_length=contest_obj.scoreboard_freeze_length,
        scoreboard_unfreeze_time=contest_obj.scoreboard_unfreeze_time,
        deactivate_time=contest_obj.deactivate_time,
        start_time_enabled=contest_obj.start_time_enabled,
        process_balloons=contest_obj.process_balloons,
        open_to_all_teams=contest_obj.open_to_all_teams,
        contest_visible_on_public_scoreboard=contest_obj.contest_visible_on_public_scoreboard,
        enabled=contest_obj.enabled,
    )

    return new_contest_obj

def get_filter_data(client_obj, contest_obj):
    """
    Get the filtered problem logs based, client object, and contest object.

    Parameters:
    client_obj (Client): The client object.
    contest_obj (Contest): The contest object.

    Returns:
    QuerySet: The filtered problem logs.
    """

    problem_logs = ProblemServerLog.objects.filter(
        server_client=client_obj,
        contest=contest_obj,
    ).order_by("-id")

    return problem_logs

def get_valid_problem_log_and_upload_process(request, problem_logs, client_obj, new_contest_obj):
    """
    Get valid problem logs and upload process.

    Args:
        request: The request object.
        problem_logs: A list of problem logs.
        client_obj: The client object.
        new_contest_obj: The new contest object.

    Returns:
        None
    """
    problem_objs_dict = dict()
    for logs in problem_logs:
        if logs.web_problem_state == "新增":
            problem_objs_dict[logs.web_problem_id] = {
                "local_id": logs.problem.id,
            }

    if problem_objs_dict:
        create_problem_log_format_and_record(
            request, client_obj, new_contest_obj, problem_objs_dict
        )

def contest_problem_copy_view(request, id, contest_id, cid):
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
    try:
        client_obj = DomServerClient.objects.get(id=id)
        problem_crawler = create_problem_crawler(client_obj)
        available_apps = get_available_apps(request)

        # Rename the contest shortname and upload the contest
        contest_shortname_rename = rename_shortname_and_handle_contest_copy_and_upload(problem_crawler, cid)

        # Create a new contest area record
        contest_obj = DomServerContest.objects.get(id=contest_id)
        new_contest_obj = create_copy_contest_record(contest_shortname_rename, contest_obj, problem_crawler)

        # Get the problem information and upload it for processing
        problem_logs = get_filter_data(client_obj, contest_obj)
        get_valid_problem_log_and_upload_process(request, problem_logs, client_obj, new_contest_obj)

        # Get all contest
        page_obj = get_contest_all_and_page_obj(request=request, client_obj=client_obj)

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
