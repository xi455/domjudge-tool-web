import hashlib

from django.core.paginator import Paginator

# from app.problems.crawler import ProblemCrawler
from app.domservers.models import DomServerContest
from utils.crawler import ProblemCrawler


class DomjudgeUser:
    def __init__(self, url: str, username: str, password: str):
        self.url = url
        self.username = username
        self.password = password


def action_display(
    function=None,
    *,
    label=None,
    description=None,
    attrs=None,
):
    def decorator(func):
        if label is not None:
            func.label = label
        if description is not None:
            func.short_description = description
        if attrs is not None:
            func.attrs = attrs
        return func

    if function is None:
        return decorator
    else:
        return decorator(function)


def testcase_md5(testcase):
    encoded_string = testcase.encode("utf-8")
    testcase_md5_hash = hashlib.md5(encoded_string).hexdigest()

    return testcase_md5_hash


def create_problem_crawler(server_client):

    url = server_client.host
    username = server_client.username
    password = server_client.mask_password

    return ProblemCrawler(url, username, password)


def get_contest_all(problem_crawler):
    contest_dicts = problem_crawler.get_contest_all()
    contest_info_list = list(contest_dicts.values())

    return contest_info_list


def get_page_obj(request, obj_list):
    for obj in obj_list:
        test = obj.contest_log.filter(web_problem_state="新增")
        obj.filtered_contest_log = test

    paginator = Paginator(obj_list, 8)
    page = request.GET.get("page")
    page_obj = paginator.get_page(page)

    return page_obj


def get_contest_all_and_page_obj(request, client_obj):
    # 獲取所有比賽信息

    if request.user.is_superuser:
        contest_info_list = [
            obj for obj in DomServerContest.objects.filter(server_client=client_obj)
        ]
    else:
        contest_info_list = DomServerContest.objects.filter(
            owner=request.user, server_client=client_obj
        )

    # 使用比賽信息列表來獲取分頁對象
    page_obj = get_page_obj(request, obj_list=contest_info_list)

    return page_obj


def upload_problem_info_process(queryset, server_object):
    """
    Process the upload of problem information for a given queryset and server object.

    Args:
        queryset (QuerySet): The queryset containing the problems to upload information for.
        server_object (Server): The server object representing the server to upload information to.

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
    upload_problem_info = dict()
    for query in queryset:
        problem_records = query.problem_log.all()
        clients_host_set = set()

        for record in problem_records:
            clients_host_set.add(record.server_client.host)

        if server_object.host not in clients_host_set:
            web_problem_state = "未上傳"
        else:
            web_problem_state = "已上傳"

        upload_problem_info[query.name] = {
            "web_problem_state": web_problem_state,
            "problem_id": query.id,
        }

    return upload_problem_info


def get_newest_problems_log(obj):
    newest_problem_log = obj.problem_log.all().order_by("-id")
    problem_logs_list = list()

    for obj in newest_problem_log:
        if obj.contest not in problem_logs_list:
            problem_logs_list.append(obj)

    return newest_problem_log
