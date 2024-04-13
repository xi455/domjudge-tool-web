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