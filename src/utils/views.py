import json

from django.contrib import admin

from app.domservers import exceptions as domserver_exceptions
from app.domservers.models import ContestRecord
from app.users.models import User
from utils.exceptions import CrawlerHandleContestShortNameException


def get_available_apps(request):
    """
    Get the available apps for the current request.

    Args:
        request: The current request object.

    Returns:
        A list of available apps.
    """
    site = admin.site
    available_apps = site.each_context(request).get("available_apps")
    print("available_apps:", available_apps)
    return available_apps


def contest_problem_shortname_process(form_data):
    """
    Process the contest problem shortname from the form data.

    Args:
        form_data (dict): The form data containing the contest and problem information.

    Returns:
        dict: The processed contest information with updated problem shortnames.

    Raises:
        CrawlerHandleContestShortNameException: If the process of contest shortname fails.
    """
    try:
        contest_info = json.loads(form_data.get("contest_data_json"))
        problem_info = json.loads(form_data.get("shortNameHidden"))

        contest_info_dict = dict()
        for key, value in contest_info.items():
            if key[21:-1] == "problem":
                contest_info_dict[value] = key[18:19]

        for data in problem_info:
            problem_shortname = (
                f'contest[problems][{contest_info_dict[data["id"]]}][shortname]'
            )
            contest_info[problem_shortname] = data["shortname"]

        return contest_info

    except Exception:
        raise CrawlerHandleContestShortNameException("Process Contest Shortname Failed")


def create_contest_record(
    request, problem_crawler, contest_shortname=None, server_client_id=None
):
    """
    Create a contest record.

    Args:
        request (HttpRequest): The HTTP request object.
        problem_crawler (ProblemCrawler): The problem crawler object.
        contest_shortname (str, optional): The shortname of the contest. Defaults to None.
        server_client_id (str, optional): The server client ID. Defaults to None.

    Raises:
        ContestRecordException: If creating the contest record fails.

    Returns:
        None
    """
    try:
        if not contest_shortname:
            contest_shortname = contest_problem_shortname_process(
                form_data=request.POST
            ).get("contest[shortname]")

        if not server_client_id:
            server_client_id = request.POST.get("server_client_id")

        cid = problem_crawler.get_contest_name_cid(contest_shortname=contest_shortname)
        owner = User.objects.get(username=request.user)

        contest_record = ContestRecord.objects.create(
            owner=owner,
            server_id=server_client_id,
            domjudge_contest_id=cid,
        )

        contest_record.save()

    except Exception:
        raise domserver_exceptions.ContestRecordException(
            "Create Contest Record Failed"
        )
