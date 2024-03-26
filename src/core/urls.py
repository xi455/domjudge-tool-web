"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path
from django.views.generic import RedirectView

from app.domservers.views.allocate import (
    contest_create_view,
    contest_information_edit_view,
    contest_copy_view,
    contest_problem_shortname_create_view,
    contest_problem_shortname_edit_view,
    contest_problem_info_upload_view,
    contest_select_problem_edit_view,
)
from app.problems.views.allocate import (
    get_contests_info_and_problem_info_api,
    problem_contest_view,
    problem_upload_view,
)
from app.users import views as user_views
from core.docs import DEFAULT_API_DOC_URL, SchemaView

apipatterns = [
    path("problem/", include("app.problems.apiurls")),
]

api_urlpatterns = [
    path("swagger/", SchemaView.with_ui(), name="swagger"),
    path("redoc/", SchemaView.with_ui(renderer="redoc"), name="redoc"),
    path("docs/", RedirectView.as_view(pattern_name=DEFAULT_API_DOC_URL), name="docs"),
    path("", include((apipatterns, "apis"))),
]

urlpatterns = [
    path("api/", include((api_urlpatterns, "api"))),
    path("admin/register/", user_views.register, name="register"),
    path("admin/", admin.site.urls),
    path("problem/", include("app.problems.urls", namespace="problem")),
    path("problem-upload/", problem_upload_view, name="problem_upload"),
    path(
        "problem-contest_updown/", problem_contest_view, name="problem_contest_updown"
    ),
    path(
        "contests-list/", get_contests_info_and_problem_info_api, name="contests_list"
    ),
    path("contest/create/", contest_create_view, name="contest_create"),
    path(
        "contest-problem/shortname/create/",
        contest_problem_shortname_create_view,
        name="contest_problem_shortname_create",
    ),
    path(
        "contest-problem/<server_user_id>/create/",
        contest_problem_info_upload_view,
        name="contest_problem_create",
    ),
    path(
        "contest/<server_user_id>/<contest_id>/<cid>/edit/page_number=<page_number>",
        contest_information_edit_view,
        name="contest_information_edit",
    ),
    path(
        "contest-problem/<server_user_id>/<cid>/shortname/edit/",
        contest_problem_shortname_edit_view,
        name="contest_problem_shortname_edit",
    ),
    path(
        "contest/<server_user_id>/<cid>/select/problem/edit/",
        contest_select_problem_edit_view,
        name="contest_select_problem_edit",
    ),
    path(
        "contest/<server_user_id>/<contest_id>/<cid>/copy/",
        contest_copy_view,
        name="contest_information_copy",
    ),
    path("", RedirectView.as_view(pattern_name="admin:index")),
]
