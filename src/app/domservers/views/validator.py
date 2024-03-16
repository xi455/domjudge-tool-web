from app.problems.models import ProblemServerLog
from utils.domserver.views import get_problem_log_web_id_list
from app.domservers.views.contest import create_problem_log_for_contest_edit

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