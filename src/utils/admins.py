import hashlib

# from app.problems.crawler import ProblemCrawler
from utils.crawler import ProblemCrawler
from django.core.paginator import Paginator


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