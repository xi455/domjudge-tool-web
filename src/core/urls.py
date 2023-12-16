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

from app.domservers.views import (
    contest_create_view,
    contest_information_edit_view,
    contest_problem_create_view,
    contest_problem_select_edit_view,
    contest_problem_upload_edit_view,
    contest_problem_copy_view,
)
from app.problems.views import contests_list_view, problem_contest_view, problem_view
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
    path("problem-upload/", problem_view, name="problem_upload"),
    path(
        "problem-contest_updown/", problem_contest_view, name="problem_contest_updown"
    ),
    path("contests-list/", contests_list_view, name="contests_list"),
    path("contest/create/", contest_create_view, name="contest_create"),
    path(
        "contest-problem/create",
        contest_problem_create_view,
        name="contest_problem_create",
    ),
    path(
        "contest/<name>/<id>/edit",
        contest_information_edit_view,
        name="contest_information_edit",
    ),
    path(
        "contest/<name>/<id>/problem-select/edit",
        contest_problem_select_edit_view,
        name="contest_problem_select_edit",
    ),
    path(
        "contest/<name>/<id>/upload/edit",
        contest_problem_upload_edit_view,
        name="contest_problem_upload_edit",
    ),
    path(
        "contest/<name>/<id>/copy",
        contest_problem_copy_view,
        name="contest_information_copy",
    ),
    path("", RedirectView.as_view(pattern_name="admin:index")),
]
