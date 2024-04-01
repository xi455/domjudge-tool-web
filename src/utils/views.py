from django.contrib import admin


def get_available_apps(request):
    """
    Get the available apps for the current request.

    Args:
        request: The current request object.

    Returns:
        A list of available apps.
    """
    site = admin.site
    available_apps = site.each_context(request).get("available_apps")
    return available_apps  # 獲取 sidebar 所有應用


def to_unicode(char):
    return "\\u" + hex(ord(char))[2:].zfill(4)


def get_str_to_unicode(string):

    for char in string:
        string = string.replace(char, to_unicode(char))

    return string