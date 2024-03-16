import json

from datetime import datetime
from django.contrib import messages

from app.domservers import exceptions as domserver_exceptions

def contest_problem_selected_shortname_process(request, old_problem_info_dict, selected_problem):
    """
    Return the id, name, shortname information of the problem
    example: [{'name': 'Hello World', 'id': '1', 'shortname': 'Hello World test'}]
    return dict format problem_id: problem_shortname
    """
    try:
        old_problem_info_keys = old_problem_info_dict.keys()
        for data in selected_problem:
            if data["id"] in old_problem_info_keys:
                data["shortname"] = old_problem_info_dict[data.get("id")]
            else:
                data["shortname"] = data.get("name")

        return selected_problem
    except Exception as e:
        messages.error(request, "處理考區簡稱失敗")
        raise domserver_exceptions.ContestShortNameException(e)


def contest_problem_information_update_process(
    request, problem_information, old_problem_information, selected_problem
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
        request=request, old_problem_info_dict=old_problem_info_dict, selected_problem=selected_problem
    )

    return problem_information, selected_problem


def contest_problem_shortname_process(request, form_data):
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

    except Exception as e:
        messages.error(request, "處理考區簡稱失敗")
        raise domserver_exceptions.ContestShortNameException(e)


def rename_shortname_and_handle_contest_copy_and_upload(request, problem_crawler, cid):
    """
    Renames the contest shortname, and handles contest copy and upload.

    Args:
        request: The HTTP request object.
        problem_crawler: An instance of the problem crawler.
        cid: The contest ID.

    Returns:
        The new contest shortname.
    """
    # Get now time
    current_time = datetime.now()
    format_time = current_time.strftime("%Y%m%d%H%M%S")

    try:
        # Get contest information
        contest_problem_information_dict = (
            problem_crawler.get_contest_or_problem_information(contest_id=cid)
        )

        # Renameing of contest shortname
        contest_shortname_rename = f"{contest_problem_information_dict['contest[shortname]']}_copy_{format_time}"
        contest_problem_information_dict["contest[shortname]"] = contest_shortname_rename

        # Create a new contest area
        result = problem_crawler.contest_and_problem_create(
            create_contest_information=contest_problem_information_dict
        )

        if result:
            return contest_shortname_rename
        else:
            messages.error(request, "考區複製上傳失敗")
            raise domserver_exceptions.ContestCopyUploadException("Error to copy test area upload.")
    
    except Exception as e:
        messages.error(request, "處理考區簡稱失敗")
        raise domserver_exceptions.ContestCopyShortNameException(e)