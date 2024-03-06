import json

from app.users.models import User
from app.problems.models import Problem
from app.problems.models import ProblemServerLog

from utils.admins import create_problem_crawler
from utils.problems.views import create_problem_log


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
    form.instance.owner = User.objects.get(username=request.user.username)
    form.instance.server_client = client_obj
    form.instance.cid = problem_crawler.get_contest_name_cid(
        contest_shortname=form.instance.short_name
    )
    form.save()


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
    create_problem_log(problems_obj_data_dict=problems_obj_data_dict)

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