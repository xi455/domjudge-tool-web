from django.shortcuts import get_object_or_404

from app.problems.models import Problem, ProblemServerLog
from app.problems.services.importer import build_zip_response


def handle_problems_upload_info(problem_data):
    """
    Handle problems upload information.

    Args:
        problem_data (dict): A dictionary containing the following keys:
            - owner_obj: The owner object.
            - contest_obj: The contest object.
            - server_client: The server client.
            - problem_id_list: A list of problem IDs.

    Returns:
        tuple: A tuple containing two elements:
            - problems_upload_info (list): A list of upload file information.
            - problems_obj_dict (dict): A dictionary mapping problem names to their corresponding objects.
    """
    owner_obj = problem_data.get("owner_obj")
    contest_obj = problem_data.get("contest_obj")
    server_client = problem_data.get("server_client")
    problem_id_list = problem_data.get("problem_id_list")

    problems_upload_info = list()
    problems_obj_dict = dict()

    for id in problem_id_list:
        problem_obj = get_object_or_404(Problem, pk=id)
        response_zip = build_zip_response(problem_obj)
        problem_zip = b"".join(response_zip.streaming_content)

        upload_file_info = (
            "problem_upload_multiple[archives][]",
            (problem_obj.name, problem_zip, "application/zip"),
        )

        problems_upload_info.append(upload_file_info)

        problems_obj_dict[problem_obj.name] = {
            "owner": owner_obj,
            "problem": problem_obj,
            "server_client": server_client,
            "contest": contest_obj,
            "web_problem_state": "新增",
        }

    return problems_upload_info, problems_obj_dict


def create_problem_log(problems_obj_data_dict):
    """
    Create problem logs based on the given dictionary of problem data.

    Args:
        problems_obj_data_dict (dict): A dictionary containing problem data.

    Returns:
        None
    """
    objs_list = list()
    for value in problems_obj_data_dict.values():
        create_problem_log_obj = ProblemServerLog(
            owner=value.get("owner"),
            problem=value.get("problem"),
            server_client=value.get("server_client"),
            web_problem_id=value.get("web_problem_id"),
            contest=value.get("contest"),
            web_problem_state=value.get("web_problem_state"),
        )
        objs_list.append(create_problem_log_obj)

    ProblemServerLog.objects.bulk_create(objs_list)
