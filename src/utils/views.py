from django.contrib import admin
def get_available_apps(request):
    site = admin.site
    available_apps = site.each_context(request).get("available_apps")
    return available_apps