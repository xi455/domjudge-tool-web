import json

from django.contrib import admin

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
    return available_apps  # 獲取 sidebar 所有應用

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