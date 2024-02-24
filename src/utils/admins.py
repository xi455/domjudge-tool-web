import hashlib

from django.core.paginator import Paginator

# from app.problems.crawler import ProblemCrawler
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


def get_page_obj(getdata, obj_list):
    paginator = Paginator(obj_list, 8)
    page = getdata.get("page")
    page_obj = paginator.get_page(page)

    return page_obj


def get_contest_all_and_page_obj(getdata, problem_crawler):
    # 獲取所有比賽信息
    contest_info_list = get_contest_all(problem_crawler)

    # 使用比賽信息列表來獲取分頁對象
    page_obj = get_page_obj(getdata, obj_list=contest_info_list)

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
        problem_record_object = (
            query.problem_log.filter(server_client=server_object)
            .order_by("-id")
            .first()
        )
        web_problem_state = (
            problem_record_object.web_problem_state if problem_record_object else "移除"
        )

        upload_problem_info[query.name] = {
            "web_problem_state": web_problem_state,
            "problem_id": query.id,
        }

    return upload_problem_info
