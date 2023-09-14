from app.problems.crawler import ProblemCrawler
import hashlib


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
