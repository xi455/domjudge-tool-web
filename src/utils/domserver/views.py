from app.users.models import User
from app.problems.models import ProblemServerLog

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
    form.instance.cid = problem_crawler.get_contest_name_cid(contest_shortname=form.instance.short_name)
    form.save()


def handle_problem_log_state(request, cid, client_obj, state, problem_crawler):
    """
    Handles the state of the problem log.

    Args:
        request: The request object.
        cid: The contest ID.
        client_obj: The client object.
        state: The state.
        problem_crawler: The problem crawler.

    Returns:
        None
    """
    owner = User.objects.get(username=request.user.username)
    problem_count = problem_crawler.get_contest_problem_count(contest_id=cid)
    problem_info = problem_crawler.get_contest_or_problem_information(contest_id=cid, need_content="problem")

    handle_problem_id_log_list = list()
    for index in range(problem_count):
        # Code continues...
        handle_problem_id_log_list.append(problem_info[f"contest[problems][{index}][problem]"])
    
    problem_log = ProblemServerLog.objects.filter(owner=owner, server_client=client_obj, web_problem_id__in=handle_problem_id_log_list)

    for obj in problem_log:
        if state == "移除":
            obj.web_problem_state = "移除"

        if state == "新增":
            obj.web_problem_state = "新增"
    
    ProblemServerLog.objects.bulk_update(problem_log, ["web_problem_state"])