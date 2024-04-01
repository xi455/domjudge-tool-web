from django.core.paginator import Paginator

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


def create_problem_crawler(server_client):

    url = server_client.host
    username = server_client.username
    password = server_client.mask_password

    return ProblemCrawler(url, username, password)


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