from django.db import IntegrityError
from django.contrib import messages
from django.shortcuts import get_object_or_404

from app.problems.models import Problem, ProblemServerLog
from app.problems.services.importer import build_zip_response_for_problem

from utils import exceptions as utils_exceptions
from app.problems import exceptions as problem_exceptions

def handle_problem_upload_format(request, problem_obj):
    """
    Handles the problem upload format.

    Args:
        request: The HTTP request object.
        problem_obj: The problem object.

    Returns:
        A tuple containing the upload file information.
    """
    try:
        response_zip = build_zip_response_for_problem(problem_obj)
        problem_zip = b"".join(response_zip.streaming_content)

        upload_file_info = (
            "problem_upload_multiple[archives][]", (f"{problem_obj.short_name}.zip", problem_zip, "application/zip"),
            problem_obj.name,
        )

        return upload_file_info
    
    except Exception as e:
        messages.error(request, "題目上傳格式錯誤!")
        raise utils_exceptions.CrawlerProblemUploadFormatException(e)

def handle_problems_upload(request, problem_data):
    """
    Handle problems upload information.

    Args:
        problem_data (dict): A dictionary containing the following keys:
            - owner_obj: The owner object.
            - contest_obj: The contest object.
            - client_obj: The server client.
            - problem_id_list: A list of problem IDs.

    Returns:
        tuple: A tuple containing two elements:
            - problems_upload_info (list): A list of upload file information.
            - problems_obj_dict (dict): A dictionary mapping problem names to their corresponding objects.
    """
    owner_obj = problem_data.get("owner_obj")
    contest_obj = problem_data.get("contest_obj")
    client_obj = problem_data.get("client_obj")

    problem_id_list = problem_data.get("problem_id_list")

    problems_upload_info = list()
    problems_obj_dict = dict()

    for id in problem_id_list:
        
        problem_obj = get_object_or_404(Problem, pk=id)
        problems_upload_info.append(handle_problem_upload_format(request, problem_obj))

        problems_obj_dict[problem_obj.name] = {
            "owner": owner_obj,
            "problem": problem_obj,
            "client_obj": client_obj,
            "contest": contest_obj,
            "web_problem_state": "新增",
        }

    return problems_upload_info, problems_obj_dict


def handle_upload_error_problem(problems_obj_data_dict, problem_crawler):
    web_problems_obj = problem_crawler.get_problems()
    local_problems_name = problems_obj_data_dict.keys()
    exist_problems_name = list()

    for name in local_problems_name:
        if name in web_problems_obj:
            exist_problems_name.append(name)
        else:
            result_name = name
            break

    web_problems_id = [web_problems_obj[name].id for name in exist_problems_name]
    for pid in web_problems_id:
        problem_crawler.delete_problem(pid)

    return result_name


def create_problem_log(request, problems_obj_data_dict):
    """
    Create problem logs based on the given dictionary of problem data.

    Args:
        problems_obj_data_dict (dict): A dictionary containing problem data.

    Returns:
        None
    """
    try:
        objs_list = list()
        for value in problems_obj_data_dict.values():
            if not value.get("web_problem_id"):
                raise problem_exceptions.ProblemUploadException("題目上傳失敗!!")
            
            create_problem_log_obj = ProblemServerLog(
                owner=value.get("owner"),
                problem=value.get("problem"),
                server_client=value.get("client_obj"),
                web_problem_id=value.get("web_problem_id"),
                contest=value.get("contest"),
                web_problem_state=value.get("web_problem_state"),
            )
            objs_list.append(create_problem_log_obj)

        ProblemServerLog.objects.bulk_create(objs_list)
        
    except IntegrityError as e:
        messages.error(request, "題目紀錄創建失敗!")
        raise problem_exceptions.ProblemCreateLogException(e)