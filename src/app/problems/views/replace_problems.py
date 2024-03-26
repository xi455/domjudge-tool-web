from django.db import IntegrityError
from django.contrib import messages
from django.shortcuts import redirect

from utils.problems.views import handle_problem_upload_format
from app.problems.models import ProblemServerLog
from app.problems import exceptions as problem_exceptions

from utils.admins import create_problem_crawler


def replace_logs_and_upload_problem(request, problem_log_objs, new_problem_obj):
    """
    Replaces the logs and uploads a new problem.

    Args:
        request: The HTTP request object.
        problem_log_objs: A list of problem log objects.
        new_problem_obj: The new problem object to be uploaded.

    Returns:
        A dictionary containing the updated problem client data.
    """
    problem_client_data = dict()
    updated_logs_obj = list()
    upload_problem_file_info = handle_problem_upload_format(request, new_problem_obj)
    
    try:
        for log in problem_log_objs:
            client_obj = log.server_client
            if client_obj not in problem_client_data:
                from app.domservers.models.dom_server import DomServerUser
                from utils.validator_pydantic import DomServerClientModel
                server_user = DomServerUser.objects.get(owner=request.user, server_client=client_obj)
                server_client = DomServerClientModel(
                    host=server_user.server_client.host,
                    username=server_user.username,
                    mask_password=server_user.mask_password,
                )

                problem_crawler = create_problem_crawler(server_client)

                (
                    is_success,
                    problems_info_dict,
                    contest_id,
                    message,
                ) = problem_crawler.upload_problem(
                    files=[upload_problem_file_info], contest_id=log.contest.cid,
                )

                if not is_success:
                    messages.error(request, message)
                    new_problem_obj.delete()
                    return redirect("/admin/problems/problem/")

                problem_client_data[client_obj] = {
                    "old_pid": log.web_problem_id,
                    "pid": problems_info_dict[new_problem_obj.name],
                    "cid": list(),
                    "server_client": server_client,
                }
            else:
                problem_client_data[client_obj]["cid"].append(log.contest.cid)
            
            log.problem = new_problem_obj
            log.web_problem_id = problem_client_data[client_obj]["pid"]
            updated_logs_obj.append(log)

        ProblemServerLog.objects.bulk_update(updated_logs_obj, ['problem', 'web_problem_id'])

        messages.success(request, "題目取代成功！！")
        return problem_client_data
    
    except IntegrityError as e:
        messages.error(request, "題目紀錄取代失敗！！")
        raise problem_exceptions.ProblemReplaceUpdateLogException(e)


def update_dj_contest_info_for_replace_problem(request, problem_log_objs, new_problem_obj):
    """
    Remove the DOMjudge Old Problem and Updates the DOMjudge contest information for replacing a problem.

    Args:
        request: The HTTP request object.
        problem_log_objs: A list of problem log objects.
        new_problem_obj: The new problem object.

    Returns:
        A redirect response to the "/admin/problems/problem/" URL.
    """
    problem_client_data = replace_logs_and_upload_problem(request, problem_log_objs, new_problem_obj)
        
    for obj, value in problem_client_data.items():
        server_client = value["server_client"]
        problem_crawler = create_problem_crawler(server_client)

        print('value["cid"]:', value["cid"])
        for cid in value["cid"]:
            problem_data_info = problem_crawler.get_contest_problems_info(cid)
            problem_data_info.append({
                "id": value["pid"],
                "name": new_problem_obj.name,
            })

            contest_info = problem_crawler.get_contest_or_problem_information(cid, need_content="contest")
            
            # 需在取得原有的problem資料
            problem_format_info = problem_crawler.problem_format_process(problem_data_info)

            contest_info.update(problem_format_info)

            result = problem_crawler.contest_problem_upload(cid, contest_info)

            if not result:
                messages.error(request, f"考區 {obj.name} 題目取代失敗！！")
                raise problem_exceptions.ProblemReplaceException("Problem replaced by Error!!")

        problem_crawler.delete_problem(request, value["old_pid"])

    messages.success(request, f"考區題目取代成功！！")
    return redirect("/admin/problems/problem/")