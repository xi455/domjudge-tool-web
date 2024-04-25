from app.users.models import User
from app.problems.models import ProblemServerLog
from app.domservers.models.dom_server import DomServerContest
from app.domservers.views.contest import create_problem_log_for_contest_edit
from app.domservers.views.demo_contest_handle import demo_contest_data, upload_demo_contest

from utils.domserver.views import get_problem_log_web_id_list

def validator_demo_contest_exist(problem_crawler, obj):
    contests = problem_crawler.get_contest_all()
    admin_owner = User.objects.get(username="admin")

    demo_contest_obj = DomServerContest.objects.filter(server_client=obj, short_name="demo")
    if "demo" not in contests and not demo_contest_obj.exists():
        
        result, demo_contset_response = upload_demo_contest(problem_crawler, admin_owner, obj)
        
        if not result:
            return False
        
        demo_contest_cid = problem_crawler.get_contest_all()["demo"].CID
        demo_contset_response.cid = demo_contest_cid
        demo_contset_response.save()

        
    if not demo_contest_obj.exists():
        demo_contest_obj_response = demo_contest_data(admin_owner, obj)
        demo_contest_obj_response.cid = contests["demo"].CID

        demo_contest_response = problem_crawler.contest_format_process(
            contest_data=demo_contest_obj_response.__dict__
        )

        demo_contest_response.update(problem_crawler.get_contest_or_problem_information(demo_contest_obj_response.cid, "problem"))
        result = problem_crawler.contest_problem_upload(
            demo_contest_obj_response.cid, demo_contest_response
        )

        if not result:
            return False
        
        demo_contest_obj_response.save()
    else:
        demo_contest_obj = demo_contest_obj.first()

    if "demo" not in contests:
        demo_contest_response = problem_crawler.contest_format_process(
            contest_data=demo_contest_obj.__dict__
        )

        problems_log_obj = ProblemServerLog.objects.filter(
            server_client=obj,
            contest=demo_contest_obj,
            web_problem_state="新增",
        )

        problems_log_dict = [{"name":obj.problem.name, "id":obj.web_problem_id} for obj in problems_log_obj]
        demo_problem_response = problem_crawler.problem_format_process(problems_log_dict)

        demo_contest_response.update(demo_problem_response)
        result = problem_crawler.contest_and_problem_create(
            create_contest_information=demo_contest_response
        )

        if not result:
            return False
        
        contests = problem_crawler.get_contest_all()
        demo_contest_obj.cid = contests["demo"].CID
        demo_contest_obj.save()
    
    return True

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


def check_create_problem_log_for_contest_edit(request, server_client, client_obj, contest_obj, form_data, problem_crawler, cid):
    """
    Check if problem logs need to be created for contest edit.

    Args:
        request: The HTTP request object.
        server_client: The server object connection information.
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
        create_problem_log_for_contest_edit(request, server_client, client_obj, contest_obj, form_data, problem_log_web_id_set, problem_logs_object)