import hashlib

from app.domservers.models import DomServerClient


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


def server_clients_all_information():
    server_clients_obj_all = DomServerClient.objects.all()
    server_clients_information = {}

    for server_obj in server_clients_obj_all:
        server_clients_information[server_obj.name] = {
            "host": server_obj.host,
            "username": server_obj.username,
            "password": server_obj.mask_password,
        }

    return server_clients_information
