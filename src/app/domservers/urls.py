from django.urls import path

from app.domservers.views import allocate as domserver_views
from app.problems.views.allocate import get_contests_info_and_problem_info_api

app_name = "domservers"

urlpatterns = [
    path(
        "contests-list/", get_contests_info_and_problem_info_api, name="contests_list"
    ),
    path("contest/create/", domserver_views.contest_create_view, name="contest_create"),
    path(
        "contest-problem/shortname/create/",
        domserver_views.contest_problem_shortname_create_view,
        name="contest_problem_shortname_create",
    ),
    path(
        "contest-problem/create/<server_user_id>/",
        domserver_views.contest_problem_info_upload_view,
        name="contest_problem_create",
    ),
    path(
        "contest/<server_user_id>/<contest_id>/<cid>/edit/page_number=<page_number>",
        domserver_views.contest_information_edit_view,
        name="contest_information_edit",
    ),
    path(
        "contest-problem/<server_user_id>/<cid>/shortname/edit/",
        domserver_views.contest_problem_shortname_edit_view,
        name="contest_problem_shortname_edit",
    ),
    path(
        "contest/<server_user_id>/<cid>/select/problem/edit/",
        domserver_views.contest_select_problem_edit_view,
        name="contest_select_problem_edit",
    ),
    path(
        "contest/<server_user_id>/<contest_id>/<cid>/copy/",
        domserver_views.contest_copy_view,
        name="contest_information_copy",
    ),
]
