import hashlib
from utils.admins import create_problem_crawler

def testcase_md5(testcase):
    encoded_string = testcase.encode("utf-8")
    testcase_md5_hash = hashlib.md5(encoded_string).hexdigest()

    return testcase_md5_hash


def get_newest_problems_log(obj):
    newest_problem_log = obj.problem_log.all().order_by("-id")
    problem_logs_list = list()

    for obj in newest_problem_log:
        if obj.contest not in problem_logs_list:
            problem_logs_list.append(obj)

    return newest_problem_log


def upload_problem_info_process(queryset, server_client):
    """
    Process the upload of problem information for a given queryset and server object.

    Args:
        queryset (QuerySet): The queryset containing the problems to upload information for.
        server_client (Server): The server client representing the server to upload information to.

    Returns:
        dict: A dictionary containing the upload information for each problem in the queryset.
              The dictionary has the following structure:
              {
                  "problem_name": {
                      "web_problem_state": "The web problem state",
                      "problem_id": "The problem ID"
                  },
                  ...
              }
    """
    problem_crawler = create_problem_crawler(server_client)
    web_problems = problem_crawler.get_problems()

    upload_problem_info = dict()
    for query in queryset:
        problem_records = query.problem_log.all()
        clients_host_set = set()

        for record in problem_records:
            clients_host_set.add(record.server_client.host)

        if server_client.host not in clients_host_set:
            web_problem_state = "未上傳"
        else:
            web_problem_state = "已上傳"

        if query.name not in web_problems:
            web_problem_state = "未上傳"
        else:
            web_problem_state = "已上傳"

        upload_problem_info[query.name] = {
            "web_problem_state": web_problem_state,
            "problem_id": query.id,
        }

    return upload_problem_info