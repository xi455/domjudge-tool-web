import datetime
import json

from datetime import datetime
from typing import Optional

import yaml

from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods
from pydantic import BaseModel, validator

from app.domservers.forms import DomServerContestCreatForm
from app.domservers.models import DomServerClient
from utils.admins import create_problem_crawler
from utils.forms import validate_country_format, validate_time_format
from utils.views import contest_initial_data_format

# Create your views here.


@require_http_methods(["GET", "POST"])
def contest_create_view(request):
    if request.method == "POST":
        form = DomServerContestCreatForm(request.POST)
        client_id = request.POST.get("client_id")

        if form.is_valid():
            print("the form is a success.")
            creat_contest_data = form.cleaned_data
            client_obj = DomServerClient.objects.get(id=client_id)

            problem_crawler = create_problem_crawler(client_obj)
            problem_data_dict = problem_crawler.get_problems()
            contest_all_name = problem_crawler.get_contest_all_name()

            if form.cleaned_data["short_name"] in contest_all_name:
                messages.error(request, "考區簡稱重複！！請重新輸入")
                return redirect(f"/contest/create/?server_client_id={client_id}")

            contest_data_json = json.dumps(creat_contest_data)
            context = {
                "client_id": client_id,
                "contest_data_json": contest_data_json,
                "problem_data_dict": problem_data_dict,
            }

            return render(request, "contest_creat_selected_problem.html", context)

    if request.method == "GET":
        initial_data = {
            "short_name": "contest",
            "name": "new contest",
            "activate_time": "-12:00:00",  # 必須得晚於 start
            "start_time": "2023-01-01 14:06:00 Asia/Taipei",
            "scoreboard_freeze_length": "+02:00:00",  # 時間得在 start - end 之間
            "end_time": "+03:00:00",
            "scoreboard_unfreeze_time": "+03:30:00",  # 解凍時間必須大於結束時間
            "deactivate_time": "+36:00:00",  # 停用時間必須大於解凍時間
        }

        form = DomServerContestCreatForm(initial=initial_data)
        client_id = request.GET.get("server_client_id")

    context = {
        "form": form,
        "client_id": client_id,
    }

    return render(request, "contest_create.html", context)


def create_contest_problem_shortname_view(request, id):
    client_obj = DomServerClient.objects.get(id=id)
    problem_crawler = create_problem_crawler(client_obj)

    if request.method == "POST":
        print("the method is a post.")

        context = {
            "client_id": client_obj.id,
        }
        return render(request, "contest_problem_edit_shortname.html", context)

    if request.method == "GET":
        print("the method is a GET.")

    context = {
        # "client_id": client_obj.id,
        # "contest_id": cid,
        # "form": form,
    }

    return render(request, "contest_problem_edit_shortname.html", context)


@require_http_methods(["POST"])
def contest_problem_process_view(request):
    client_id = request.POST.get("client_id")
    contest_data = json.loads(request.POST.get("contestDataJson"))
    selected_problem_dict = json.loads(request.POST.get("selectedCheckboxes"))

    client_obj = DomServerClient.objects.get(id=client_id)
    problem_crawler = create_problem_crawler(client_obj)

    contest_information = problem_crawler.contest_format_process(contest_data=contest_data)
    problem_information = problem_crawler.problem_format_process(problem_data=selected_problem_dict)

    contest_information.update(problem_information)
    contest_information.update({"contest[save]": ""})
    create_information = contest_information

    # test------------------------
    create_data_json = json.dumps(create_information)
    print("selected_problem_dict:", selected_problem_dict)

    context = {
        "server_client_id": client_id,
        "create_data_json": create_data_json,
        "selected_problem_dict": selected_problem_dict,
    }

    return render(request, "contest_problem_shortname_create.html", context)
    # test end------------------------

    # create_response = problem_crawler.contest_and_problem_create(
    #     create_contest_information=create_information
    # )

    # if create_response:
    #     messages.success(request, "考區創建成功！！")
    # else:
    #     messages.error(request, "考區創建失敗！！")

    # contest_dicts = problem_crawler.get_contest_all()

    # context = {
    #     "contest_dicts": contest_dicts,
    #     "server_client_id": client_id,
    # }

    # return render(request, "contest_list.html", context)


def contest_initial_data_format(initial_data: dict):

    # Convert contest data to the same format.

    for key, value in initial_data.items():

        if value == "":
            continue

        if key in ("short_name", "name") or isinstance(value, bool):
            continue

        if key == "start_time":
            initial_data[key] = validate_country_format(time_string=value)
            continue

        if len(value) > 9 and key != "start_time":
            continue

        if validate_time_format(time_string=value) is False:
            initial_data[key] = f"{value}:00"

    return initial_data


def contest_information_edit_view(request, id, cid):

    client_obj = DomServerClient.objects.get(id=id)
    problem_crawler = create_problem_crawler(client_obj)

    if request.method == "POST":
        print("the method is a post.")

        print("data:", request.POST)
        form = DomServerContestCreatForm(request.POST)

        if form.is_valid():
            print("the form is a success.")
            contest_update_data = form.cleaned_data

            for key, value in contest_update_data.items():
                if isinstance(value, bool):
                    if value:
                        contest_update_data[key] = "1"
                    else:
                        contest_update_data[key] = "0"

            # get the all problem
            problem_data_dict = problem_crawler.get_problems()
            contest_update_data_json = json.dumps(contest_update_data)

            # get the existing problem
            existing_problem_informtion_dict = (
                problem_crawler.get_contest_or_problem_information(
                    contest_id=cid, need_content="problem"
                )
            )
            existing_problem_id_list = [
                value
                for key, value in existing_problem_informtion_dict.items()
                if "[problem]" in key
            ]

            context = {
                "client_id": client_obj.id,
                "contest_id": cid,
                "contest_update_data_json": contest_update_data_json,
                "existing_problem_id_list": existing_problem_id_list,
                "problem_data_dict": problem_data_dict,
            }
            return render(request, "contest_edit_selected_problem.html", context)

    if request.method == "GET":
        print("the method is a GET.")

        (contest_info_response) = problem_crawler.get_contest_or_problem_information(
            contest_id=cid, need_content="contest"
        )

        form = DomServerContestCreatForm()

        initial_data = {
            "short_name": contest_info_response["contest[shortname]"],
            "name": contest_info_response["contest[name]"],
            "activate_time": contest_info_response["contest[activatetimeString]"],
            "start_time": contest_info_response["contest[starttimeString]"],
            "scoreboard_freeze_length": contest_info_response[
                "contest[freezetimeString]"
            ],
            "end_time": contest_info_response["contest[endtimeString]"],
            "scoreboard_unfreeze_time": contest_info_response[
                "contest[unfreezetimeString]"
            ],
            "deactivate_time": contest_info_response["contest[deactivatetimeString]"],
            "start_time_enabled": True
            if contest_info_response["contest[starttimeEnabled]"] == "1"
            else False,
            "process_balloons": True
            if contest_info_response["contest[processBalloons]"] == "1"
            else False,
            "contest_visible_on_public_scoreboard": True
            if contest_info_response["contest[public]"] == "1"
            else False,
            "open_to_all_teams": True
            if contest_info_response["contest[openToAllTeams]"] == "1"
            else False,
            "enabled": True
            if contest_info_response["contest[enabled]"] == "1"
            else False,
        }
        # print("initial_data:", initial_data)
        initial_data = contest_initial_data_format(initial_data=initial_data)

        form = DomServerContestCreatForm(initial=initial_data)

    context = {
        "client_id": client_obj.id,
        "contest_id": cid,
        "form": form,
    }

    return render(request, "contest_edit.html", context)


def contest_info_update_process(problem_crawler, contest_data, cid):

    # Returns whether the contest editor is successful or not

    contest_update_information = problem_crawler.contest_format_process(
        contest_data=contest_data
    )
    update_response = problem_crawler.contest_info_update(
        contest_id=cid, contest_data_dict=contest_update_information
    )

    return update_response


def problem_info_update_process(problem_crawler, selected_problem, cid):

    # Returns whether the problem editor was successful or not

    old_problem_information = problem_crawler.get_contest_or_problem_information(
        contest_id=cid, need_content="problem"
    )

    problem_need_delete = old_problem_information

    if problem_need_delete:
        problem_need_delete_id = [
            value for key, value in problem_need_delete.items() if "[problem]" in key
        ]

        for problem_id in problem_need_delete_id:
            problem_crawler.delete_contest_problem(
                contest_id=cid, web_problem_id=problem_id
            )

    problem_upload_information = problem_crawler.problem_format_process(
        problem_data=selected_problem
    )

    upload_response = problem_crawler.contest_problem_upload(
        contest_id=cid, problem_data=problem_upload_information
    )

    return upload_response


def contest_problem_upload_edit_view(request, id, cid):
    contest_data = json.loads(request.POST.get("contestDataJson"))
    selected_problem = json.loads(request.POST.get("selectedCheckboxes"))

    client_obj = DomServerClient.objects.get(id=id)
    problem_crawler = create_problem_crawler(client_obj)

    contest_update_response = contest_info_update_process(
        problem_crawler=problem_crawler, contest_data=contest_data, cid=cid
    )

    if contest_update_response:
        messages.success(request, "考區編輯成功！！")
    else:
        messages.error(request, "考區編輯失敗！！")

    problem_upload_response = problem_info_update_process(
        problem_crawler=problem_crawler, selected_problem=selected_problem, cid=cid
    )

    if problem_upload_response:
        messages.success(request, "考區題目編輯成功！！")
    else:
        messages.error(request, "考區題目編輯失敗！！")

    contest_dicts = problem_crawler.get_contest_all()

    context = {
        "contest_dicts": contest_dicts,
        "server_client_id": client_obj.id,
    }

    return render(request, "contest_list.html", context)


def contest_problem_copy_view(request, id, cid):
    client_obj = DomServerClient.objects.get(id=id)
    problem_crawler = create_problem_crawler(client_obj)

    # get now time
    current_time = datetime.now()
    format_time = current_time.strftime("%Y%m%d%H%M%S")

    # get contest information
    contest_problem_information_dict = (
        problem_crawler.get_contest_or_problem_information(contest_id=cid)
    )

    # renameing of contest
    contest_problem_information_dict[
        "contest[shortname]"
    ] = f"{contest_problem_information_dict['contest[shortname]']}_copy_{format_time}"
    problem_crawler.contest_and_problem_create(
        create_contest_information=contest_problem_information_dict
    )

    # get all contest
    contest_dicts = problem_crawler.get_contest_all()

    context = {
        "contest_dicts": contest_dicts,
        "server_client_id": client_obj.id,
    }

    return render(request, "contest_list.html", context)
