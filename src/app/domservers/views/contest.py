import json

from django.db import IntegrityError
from django.contrib import messages

from app.users.models import User
from app.problems.models import ProblemServerLog
from app.domservers.models.dom_server import DomServerContest
from app.domservers import exceptions as domserver_exceptions

from utils.domserver.views import create_problem_log_format_and_record


def get_contest_selected_problem_local_id(form_data):
    """
    Get the local ID of the selected problem in the contest.

    Args:
        form_data (dict): The form data containing the problem information.

    Returns:
        dict: Returning problem content dict.
    """
    problem_info = json.loads(form_data.get("shortNameHidden"))
    
    problem_info_dict = dict()
    for data in problem_info:
        problem_info_dict[data.get("id")] = data

    return problem_info_dict


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


def create_copy_contest_record(request, contest_shortname_rename, contest_obj, problem_crawler):
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

    try:
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
    except IntegrityError as e:
        messages.error(request, "考區創建失敗！")
        raise domserver_exceptions.ContestCreateException(e)
    

def get_copy_problem_log_and_upload_process(request, problem_logs, client_obj, new_contest_obj):
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