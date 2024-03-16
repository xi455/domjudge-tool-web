import json
from django.db import IntegrityError
from django.contrib import messages

from app.users.models import User
from app.problems.models import Problem
from app.problems.models import ProblemServerLog

from utils.admins import create_problem_crawler
from utils.problems.views import create_problem_log

from app.domservers import exceptions as domserver_exceptions
from utils import exceptions as utils_exceptions


def create_contest_record(request, form, client_obj, problem_crawler):
    """
    Create a contest.

    Args:
        request: The HTTP request object.
        form: The form object containing the contest data.
        client_obj: The client object representing the server.
        problem_crawler: The problem crawler object.

    Returns:
        None
    """
    try:
        form.instance.owner = User.objects.get(username=request.user.username)
        form.instance.server_client = client_obj
        form.instance.cid = problem_crawler.get_contest_name_cid(
            contest_shortname=form.instance.short_name
        )
        form.save()
    except IntegrityError as e:
        messages.error(request, "考區創建失敗！")
        raise domserver_exceptions.ContestCreateException(e)


def get_problem_log_web_id_list(cid, problem_crawler):
    """
    Get a list of problem log web IDs for a given contest ID.

    Args:
        cid (int): The contest ID.
        problem_crawler (ProblemCrawler): An instance of the ProblemCrawler class.

    Returns:
        list: A list of problem log web IDs.
    """
    problem_count = problem_crawler.get_contest_problem_count(contest_id=cid)
    problem_info = problem_crawler.get_contest_or_problem_information(
        contest_id=cid, need_content="problem"
    )

    problem_log_web_id_list = list()
    for index in range(problem_count):
        problem_log_web_id_list.append(
            problem_info[f"contest[problems][{index}][problem]"]
        )

    return problem_log_web_id_list


def create_problem_log_format_and_record(
    request, client_obj, contest_obj, problem_info_dict, no_existing_problem_id_set=None
):
    """
    Create problem log format and record.

    Args:
        request: The request object.
        client_obj: The client object.
        contest_obj: The contest object.
        problem_info_dict: The dictionary containing problem information.
        no_existing_problem_id_set: Set of problem IDs that do not exist yet (optional).

    Returns:
        None
    """
    owner = User.objects.get(username=request.user.username)
    problem_crawler = create_problem_crawler(client_obj)

    if no_existing_problem_id_set is None:
        problem_id_list = get_problem_log_web_id_list(
            contest_obj.cid, problem_crawler
        )
    else:
        problem_id_list = [_ for _ in no_existing_problem_id_set]

    problems_obj_data_dict = dict()
    for id in problem_id_list:
        local_id = problem_info_dict.get(id).get("local_id")
        problem_obj = Problem.objects.get(id=local_id)

        problems_obj_data_dict.update(
            {
                f"problem_{id}": {
                    "owner": owner,
                    "problem": problem_obj,
                    "server_client": client_obj,
                    "web_problem_id": id,
                    "contest": contest_obj,
                    "web_problem_state": "新增",
                }
            }
        )
    create_problem_log(request=request, problems_obj_data_dict=problems_obj_data_dict)

def update_problem_log_state(request, state, client_obj, contest_obj):
    """
    Update the problem log state in the ProblemServerLog objects based on the given state.

    Args:
        request: The HTTP request object.
        state (str): The state to update the web problem to. Can be "移除" or "新增".
        client_obj: The client object.
        contest_obj: The contest object.

    Returns:
        None
    """
    owner = User.objects.get(username=request.user.username)
    problem_crawler = create_problem_crawler(client_obj)
    
    problem_log_web_id_list = get_problem_log_web_id_list(
        contest_obj.cid, problem_crawler
    )

    problem_log = ProblemServerLog.objects.filter(
        server_client=client_obj,
        contest=contest_obj,
        web_problem_id__in=problem_log_web_id_list,
    )

    for obj in problem_log:
        if state == "移除":
            obj.web_problem_state = "移除"

        if state == "新增":
            obj.web_problem_state = "新增"


    ProblemServerLog.objects.bulk_update(problem_log, ["web_problem_state"])


def handle_problem_log(form_data, request, client_obj, contest_obj):
    """
    Handle problem log.

    Args:
        form_data (dict): The form data.
        request (HttpRequest): The HTTP request object.
        client_obj (Client): The client object.
        contest_obj (Contest): The contest object.

    Returns:
        None
    """
    problem_info_list = json.loads(form_data.get("shortNameHidden"))
    problem_info_dict = dict()
    for data in problem_info_list:
        problem_info_dict[data.get("id")] = data

    create_problem_log_format_and_record(
        request, client_obj, contest_obj, problem_info_dict
    )


def old_problem_info_remove_process(request, problem_crawler, cid):
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

    except Exception as e:
        messages.error(request, "移除舊題目資訊時發現錯誤")
        raise utils_exceptions.CrawlerRemoveContestOldProblemsException(e)