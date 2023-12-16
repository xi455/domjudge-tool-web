import datetime
import json

from datetime import datetime
from typing import Optional

import yaml

from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods
from pydantic import BaseModel, validator

from app.domservers.forms import DomServerContestCreatForm
from app.domservers.models import DomServerClient
from utils.admins import create_problem_crawler

# Create your views here.


# class ContestYaml(BaseModel):
#     name: Optional[str] = None
#     short_name: Optional[str] = None
#     start_time: Optional[datetime.datetime] = None
#     duration: Optional[int] = None
#     scoreboard_freeze_length: Optional[int] = None
#     penalty_time: Optional[int] = None

#     @validator("scoreboard_freeze_length", pre=True)
#     def parse_scoreboard_freeze_length(cls, value):

#         if value is None:
#             return None
#         elif isinstance(value, int):
#             return value
#         elif isinstance(value, str):
#             try:
#                 print("hllo world")
#                 # 嘗試將字符串解析為整數
#                 time_object = datetime.strptime(value, "%H:%M:%S").time()

#                 time_in_seconds = (
#                     time_object.hour * 3600
#                     + time_object.minute * 60
#                     + time_object.second
#                 )
#                 return time_in_seconds
#             except ValueError:
#                 raise ValueError("Unable to parse string as an integer.")


@require_http_methods(["GET", "POST"])
def contest_create_view(request):
    if request.method == "POST":
        form = DomServerContestCreatForm(request.POST)
        client_name = request.POST.get("client_name")

        if form.is_valid():
            print("the form is a success.")
            creat_contest_data = form.cleaned_data

            client_obj = DomServerClient.objects.get(name=client_name)
            problem_crawler = create_problem_crawler(client_obj)
            problem_data_dict = problem_crawler.get_problems()

            contest_data_json = json.dumps(creat_contest_data)
            context = {
                "client_name": client_name,
                "contest_data_json": contest_data_json,
                "problem_data_dict": problem_data_dict,
            }

            return render(request, "admin/contest_selected_problem.html", context)
        else:
            print("the form is a danger.")

    else:
        # form = DomServerContestCreatForm()

        # 測試________________
        initial_data = {
            "short_name": "contest",
            "name": "new contest",
            "activate_time": "-12:00:00",  # 必須得晚於 start
            "start_time": "2023-01-01 14:06:00 Asia/Taipei",
            "scoreboard_freeze_length": "+02:00:00",  # 時間得在 start - end 之間
            "end_time": "+03:00:00",
            "scoreboard_unfreeze_time": "+03:30:00",  # 解凍時間必須大於結束時間
            "deactivate_time": "+36:00:00",  # 停用時間必須大於解凍時間
            # "duration": "+02:00:00",
            # "penalty_time": "20",
            # 其他字段的初始值
        }

        form = DomServerContestCreatForm(initial=initial_data)
        # 測試_____________end
        client_name = request.GET.get("server_client_name")

    context = {
        "form": form,
        "client_name": client_name,
    }

    return render(request, "admin/contest_add.html", context)


def contest_problem_create_view(request):
    client_name = request.POST.get("client_name")
    contest_data = json.loads(request.POST.get("contestDataJson"))
    selected_problem = json.loads(request.POST.get("selectedCheckboxes"))

    contest_information = {
        "contest[shortname]": contest_data.get("short_name"),
        "contest[name]": contest_data.get("name"),
        "contest[activatetimeString]": contest_data.get("activate_time"),
        "contest[starttimeString]": contest_data.get("start_time"),
        "contest[starttimeEnabled]": contest_data.get("start_time_enabled"),
        "contest[freezetimeString]": contest_data.get("scoreboard_freeze_length"),
        "contest[endtimeString]": contest_data.get("end_time"),
        "contest[unfreezetimeString]": contest_data.get("scoreboard_unfreeze_time"),
        "contest[deactivatetimeString]": contest_data.get("deactivate_time"),
        "contest[processBalloons]": contest_data.get("process_balloons"),
        "contest[public]": contest_data.get("contest_visible_on_public_scoreboard"),
        "contest[openToAllTeams]": contest_data.get("open_to_all_teams"),
        "contest[enabled]": contest_data.get("enabled"),
    }

    for key, value in contest_information.items():
        if value and isinstance(value, bool):
            contest_information[key] = "1"

    problem_information = dict()
    for count in range(len(selected_problem)):
        problem_information.update(
            {
                f"contest[problems][{count}][problem]": selected_problem[count].get(
                    "id"
                ),
                f"contest[problems][{count}][shortname]": selected_problem[count].get(
                    "name"
                ),
                f"contest[problems][{count}][points]": "1",
                f"contest[problems][{count}][allowSubmit]": "1",
                f"contest[problems][{count}][allowJudge]": "1",
                f"contest[problems][{count}][color]": "",
                f"contest[problems][{count}][lazyEvalResults]": "0",
            }
        )
    problem_information.update({"contest[save]": ""})

    create_contest_information = contest_information
    create_contest_information.update(problem_information)

    client_obj = DomServerClient.objects.get(name=client_name)

    problem_crawler = create_problem_crawler(client_obj)
    create_response = problem_crawler.contest_and_problem_create(
        create_contest_information=create_contest_information
    )

    return render(request, "admin/get_contests.html")


def contest_information_edit_view(request, name, id):
    client_obj = DomServerClient.objects.get(name=name)
    problem_crawler = create_problem_crawler(client_obj)

    (
        contest_info_response,
        problem_info_list_response,
    ) = problem_crawler.get_contest_or_problem_information(
        contest_id=id, need_content="contest"
    ), problem_crawler.get_contest_or_problem_information(
        contest_id=id, need_content="problem"
    )

    problem_id_info_list = [
        value for key, value in problem_info_list_response.items() if "[problem]" in key
    ]

    form = DomServerContestCreatForm()

    initial_data = {
        "short_name": contest_info_response["contest[shortname]"],
        "name": contest_info_response["contest[name]"],
        "activate_time": contest_info_response["contest[activatetimeString]"],
        "start_time": contest_info_response["contest[starttimeString]"],
        "scoreboard_freeze_length": contest_info_response["contest[freezetimeString]"],
        "end_time": contest_info_response["contest[endtimeString]"],
        "scoreboard_unfreeze_time": contest_info_response[
            "contest[unfreezetimeString]"
        ],
        "deactivate_time": contest_info_response["contest[deactivatetimeString]"],
        "start_time_enabled": contest_info_response["contest[starttimeEnabled]"],
        "process_balloons": contest_info_response["contest[processBalloons]"],
        "contest_visible_on_public_scoreboard": contest_info_response[
            "contest[public]"
        ],
        "open_to_all_teams": contest_info_response["contest[openToAllTeams]"],
        "enabled": contest_info_response["contest[enabled]"],
    }

    form = DomServerContestCreatForm(initial=initial_data)

    context = {
        "client_name": name,
        "contest_id": id,
        "form": form,
        "problem_id_info_list": problem_id_info_list,
    }

    return render(request, "admin/contest_edit.html", context)


def contest_problem_select_edit_view(request, name, id):
    if request.method == "POST":

        form = DomServerContestCreatForm(request.POST)

        if form.is_valid():
            print("the form is a success.")
            contest_update_data = form.cleaned_data

            client_obj = DomServerClient.objects.get(name=name)
            problem_crawler = create_problem_crawler(client_obj)
            problem_data_dict = problem_crawler.get_problems()

            contest_update_data_json = json.dumps(contest_update_data)

            existing_problem_id_list = request.POST.get("problem_id_list")

            context = {
                "client_name": name,
                "contest_id": id,
                "contest_update_data_json": contest_update_data_json,
                "existing_problem_id_list": existing_problem_id_list,
                "problem_data_dict": problem_data_dict,
            }
            return render(request, "admin/contest_selected_problem_edit.html", context)


def contest_problem_upload_edit_view(request, name, id):
    contest_data = json.loads(request.POST.get("contestDataJson"))
    selected_problem = json.loads(request.POST.get("selectedCheckboxes"))

    contest_information = {
        "contest[shortname]": contest_data.get("short_name"),
        "contest[name]": contest_data.get("name"),
        "contest[activatetimeString]": contest_data.get("activate_time"),
        "contest[starttimeString]": contest_data.get("start_time"),
        "contest[starttimeEnabled]": contest_data.get("start_time_enabled"),
        "contest[freezetimeString]": contest_data.get("scoreboard_freeze_length"),
        "contest[endtimeString]": contest_data.get("end_time"),
        "contest[unfreezetimeString]": contest_data.get("scoreboard_unfreeze_time"),
        "contest[deactivatetimeString]": contest_data.get("deactivate_time"),
        "contest[processBalloons]": contest_data.get("process_balloons"),
        "contest[public]": contest_data.get("contest_visible_on_public_scoreboard"),
        "contest[openToAllTeams]": contest_data.get("open_to_all_teams"),
        "contest[enabled]": contest_data.get("enabled"),
    }

    for key, value in contest_information.items():
        if value and isinstance(value, bool):
            contest_information[key] = "1"

    problem_information = dict()
    for count in range(len(selected_problem)):
        problem_information.update(
            {
                f"contest[problems][{count}][problem]": selected_problem[count].get("id"),
                f"contest[problems][{count}][shortname]": selected_problem[count].get("name"),
                f"contest[problems][{count}][points]": "1",
                f"contest[problems][{count}][allowSubmit]": "1",
                f"contest[problems][{count}][allowJudge]": "1",
                f"contest[problems][{count}][color]": "",
                f"contest[problems][{count}][lazyEvalResults]": "0",
            }
        )

    print("update_contest_information:")

    for key, value in problem_information.items():
        print(key, value, type(value))

    client_obj = DomServerClient.objects.get(name=name)
    problem_crawler = create_problem_crawler(client_obj)

    old_problem_information = problem_crawler.get_contest_or_problem_information(
        contest_id=id, need_content="problem"
    )

    if problem_information:
        problem_need_delete = {key: value for key, value in old_problem_information.items() if key not in problem_information}
        problem_need_update = problem_information

    else:
        problem_need_delete = old_problem_information
        problem_need_update = dict()

    problem_crawler.contest_problem_update(
        contest_id=id, contest_data_dict=contest_information
    )

    if problem_need_delete:
        problem_need_delete_id = [value for key, value in problem_need_delete.items() if "[problem]" in key]
    
        for problem_id in problem_need_delete_id:
            problem_crawler.delete_contest_problem(contest_id=id, web_problem_id=problem_id)
    
    if problem_need_update:
        problem_crawler.contest_problem_upload(contest_id=id, problem_data=problem_need_update)

    return render(request, "admin/get_contests.html")

def contest_problem_copy_view(request, name, id):
    client_obj = DomServerClient.objects.get(name=name)
    problem_crawler = create_problem_crawler(client_obj)

    current_time = datetime.now()
    format_time = current_time.strftime("%Y%m%d%H%M%S")
    
    contest_problem_information_dict = problem_crawler.get_contest_or_problem_information(contest_id=id)

    contest_problem_information_dict["contest[shortname]"] = f"{contest_problem_information_dict['contest[shortname]']}_copy_{format_time}"
    print("contest_problem_information_dict:", contest_problem_information_dict)    
    problem_crawler.contest_and_problem_create(create_contest_information=contest_problem_information_dict)

    return render(request, "admin/get_contests.html")