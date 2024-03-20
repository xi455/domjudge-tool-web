import json

from datetime import datetime
from enum import Enum
from typing import Optional

import requests

from bs4 import BeautifulSoup
from django.contrib import messages
from pydantic import BaseModel, validator

from utils.views import get_str_to_unicode

from app.problems import exceptions as problems_exceptions
from utils import exceptions as utils_exceptions


class TestCase(BaseModel):
    id: str
    file_id: str


class ServerContest(BaseModel):
    contest_name: str
    contest_id: str


class ContestInfo(BaseModel):
    CID: Optional[str] = None
    name: Optional[str] = None
    shortname: Optional[str] = None
    activate: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    processballoons: Optional[str] = None
    public: Optional[str] = None
    teams: Optional[str] = None
    problems: Optional[str] = None


class ContestDetails(BaseModel):
    contest_name: str
    contest_info: ContestInfo


class ProblemInfo(BaseModel):
    id: str
    name: str


class HomePath(str, Enum):
    LOGIN = "/login"
    JURY = "/jury"


class ProblemPath(str, Enum):
    GET = "/jury/problems"
    POST = "/jury/problems"
    EDIT = "/jury/problems/{}/edit"
    DELETE = "/jury/problems/{}/delete"


class ConTestPath(str, Enum):
    GET = "/jury/contests"
    GET_PROBLEM = "/jury/contests/{}"
    GET_SINGLE_EDIT = "/jury/contests/{}/edit"
    POST = "/jury/contests/add"
    POST_SINGLE = "/jury/contests/{}/edit"
    POST_SINGLE_EDIT = "/jury/contests/{}/edit"
    DELETE = "/jury/contests/{}/problems/{}/delete"


class TestCasePath(str, Enum):
    GET = "/jury/problems/{}/testcases"
    GET_INPUT = "/jury/problems/{}/testcases/{}/fetch/input"
    GET_OUTPUT = "/jury/problems/{}/testcases/{}/fetch/output"
    DELETE = "/jury/problems/{}/delete_testcase"


class ApiPath(str, Enum):
    CONTEST_YAML = "/api/v4/contests/{}/contest-yaml"
    CONTEST_POST = "/api/v4/contests"


class ProblemCrawler:
    def __init__(self, url: str, username: str, password: str):
        self.url = url
        self.username = username
        self.password = password

    @property
    def session(self):
        if not hasattr(self, "_session"):
            self._session = self.login()

        return self._session

    def login(self):
        session = requests.Session()
        page = session.get(self.url + HomePath.LOGIN)
        soup = BeautifulSoup(page.text, "html.parser")
        data = {ele.get("name"): ele.get("value") for ele in soup.select("input")}
        data["_username"] = self.username
        data["_password"] = self.password

        response = session.post(self.url + HomePath.LOGIN, data=data)

        if response.url == self.url + HomePath.JURY:
            return session

        raise problems_exceptions.ProblemDownloaderLoginException("Login Error.")

    def misjudgment(self, page):
        """
        Determine whether there are upload errors.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object representing the HTML page.

        Returns:
            bool: True if there are no upload errors, False otherwise.
        """
        soup = BeautifulSoup(page.text, "html.parser")

        error_elements = soup.select_one(".form-error-message")
        if error_elements and page.status_code != 200:
            return False
        else:
            return True

    def get_contest_name(self, contests_id):
        page = self.session.get(self.url + ConTestPath.GET)
        soup = BeautifulSoup(page.text, "html.parser")

        table_elements = soup.select(
            "table",
            {
                "class": "data-table table table-sm table-striped dataTable no-footer",
                "id": "DataTables_Table_0",
            },
        )

        tr_elements = table_elements[-1].select("tbody tr")

        for tr in tr_elements:
            td_elements = tr.select("td")
            web_contest_id = td_elements[0].text.strip()
            if web_contest_id == contests_id:
                web_contest_name = td_elements[1].text.strip()

                return web_contest_name

    def get_contest_all_name(self):
        data = self.get_contest_all()

        return data.keys()

    def get_contest_name_cid(self, contest_shortname):
        contests = self.get_contest_all()
        for key, value in contests.items():
            if value.shortname == contest_shortname:
                return value.CID

        raise utils_exceptions.CrawlerGetContestCidException("找不到對應的考區ID")

    def get_contest_all(self):

        # get the all domjudge contest.

        page = self.session.get(self.url + ConTestPath.GET)

        soup = BeautifulSoup(page.text, "html.parser")

        table_elements = soup.select(
            "table",
            {
                "class": "data-table table table-sm table-striped dataTable no-footer",
                "id": "DataTables_Table_0",
            },
        )

        thead_elements = table_elements[-1].select("thead th")
        tr_elements = table_elements[-1].select("tbody tr")
        contests_detail_dict = dict()

        button_without_title = 2
        for tr_element in tr_elements:

            td_elements = tr_element.select("td")
            contest_shortname = td_elements[1].text.strip()
            contest_info_dict = dict()
            for index in range(len(thead_elements) - button_without_title):

                thead = (
                    thead_elements[index]
                    .text.strip()
                    .replace("?", "")
                    .replace("# ", "")
                )
                td = td_elements[index].text.strip()
                contest_info_dict[thead] = td

            contest_details = ContestInfo(**contest_info_dict)
            contests_detail_dict[contest_shortname] = contest_details

        return contests_detail_dict

    def get_problems(self):

        # get domjudge all problem information return class type
        # example: {problem_name: class(id=problem_id, name=problem_name)}

        page = self.session.post(self.url + ProblemPath.GET)
        soup = BeautifulSoup(page.text, "html.parser")

        problem_data_dict = dict()
        tr_elements = soup.select("table tr")
        for index in range(1, len(tr_elements)):
            td_elements = tr_elements[index].select("td")

            id = td_elements[0].text.strip()
            name = td_elements[1].text.strip()

            problem_info = {
                "id": id,
                "name": name,
            }

            problem_obj = ProblemInfo(**problem_info)
            problem_data_dict[name] = problem_obj

        return problem_data_dict

    def validate_problem_name_repeat(self, problem_name_list):
        result = []
        problem_dict = self.get_problems()
        problem_name = problem_dict.keys()
        for name in problem_name_list:
            if name in problem_name:
                result.append(name)

        if result:
            return False, result

        return True, None

    def upload_problem(self, files, contest_id):

        data = {
            "problem_upload_multiple[contest]": contest_id,
        }

        problem_name_list = []
        for index in range(len(files)):
            problem_name_list.append(files[index][1][0])
            str_to_unicode = get_str_to_unicode(files[index][1][0])
            files[index] = [_ for _ in files[index]]
            files[index][1] = [_ for _ in files[index][1]]
            files[index][1][0] = str_to_unicode

        is_valid, repeat_name_list = self.validate_problem_name_repeat(
            problem_name_list
        )
        if not is_valid:
            repeat_name = ", ".join(repeat_name_list)
            message = f"上傳失敗！！{repeat_name} 題目名稱已與伺服器內題目重名。"
            return False, {}, contest_id, message

        page = self.session.post(self.url + ProblemPath.POST, data=data, files=files)
        result = self.misjudgment(page)
        
        if result:
            is_succeed = True
        else:
            message = "題目上傳失敗！！"
            return False, {}, contest_id, message

        result_problems_info_dict = dict()
        problems_dict = self.get_problems()
        problems_key = problems_dict.keys()
        for name in problem_name_list:
            if name in problems_key:
                result_problems_info_dict[name] = problems_dict[name].id

        return is_succeed, result_problems_info_dict, contest_id, None

    def problem_format_process(self, problem_data):
        problem_information = dict()
        for count in range(len(problem_data)):
            problem_information.update(
                {
                    f"contest[problems][{count}][shortname]": problem_data[count].get(
                        "name"
                    ),
                    f"contest[problems][{count}][points]": "1",
                    f"contest[problems][{count}][color]": "",
                }
            )

        for count in range(len(problem_data)):
            problem_information.update(
                {
                    f"contest[problems][{count}][problem]": problem_data[count].get(
                        "id"
                    ),
                    f"contest[problems][{count}][allowSubmit]": "1",
                    f"contest[problems][{count}][allowJudge]": "1",
                    f"contest[problems][{count}][lazyEvalResults]": "0",
                }
            )

        return problem_information

    def contest_format_process(self, contest_data):
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
            if value is True:
                contest_information[key] = "1"

            if value is False:
                contest_information[key] = "0"

        return contest_information

    def get_contest_problem_count(self, contest_id):
        page = self.session.get(
            self.url + ConTestPath.GET_SINGLE_EDIT.format(contest_id)
        )
        
        soup = BeautifulSoup(page.text, "html.parser")
        thead_elements = soup.select(".table thead")

        tbody = ""
        for thead in thead_elements:
            tbody = thead.find_next_sibling("tbody")

        if tbody:
            tr_elements_length = len(tbody.select("tr"))
            return tr_elements_length

        return 0

    def get_contests_list_all(self):
        page = self.session.get(self.url + ConTestPath.GET)
        soup = BeautifulSoup(page.text, "html.parser")

        table_elements = soup.select(
            "table",
            {
                "class": "data-table table table-sm table-striped dataTable no-footer",
                "id": "DataTables_Table_0",
            },
        )
        tr_elements = table_elements[-1].select("tbody tr")

        server_contests_info_dict = dict()
        for tr in tr_elements:
            td_elements = tr.select("td")
            web_contest_id = td_elements[0].text.strip()
            web_contest_name = td_elements[1].text.strip()

            contest_info = {
                "contest_name": web_contest_name,
                "contest_id": web_contest_id,
            }

            server_contest = ServerContest(**contest_info)
            server_contests_info_dict[web_contest_name] = server_contest

        return server_contests_info_dict

    def contest_and_problem_create(self, create_contest_information):

        # Post the contest area creation information and upload it to
        # domjudge to create a new contest area.

        # return the bool to see if it succeeded.

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        if "contest[save]" not in create_contest_information:
            create_contest_information.update({"contest[save]": ""})

        if (
            ("contest[teams][]") in create_contest_information
            and "contest[teamCategories][]" in create_contest_information
        ):
            del create_contest_information["contest[teams][]"]
            del create_contest_information["contest[teamCategories][]"]

        page = self.session.post(
            self.url + ConTestPath.POST,
            data=create_contest_information,
            headers=headers,
        )

        return self.misjudgment(page)

    def get_contest_problems_info(self, contest_id):

        problem_count = self.get_contest_problem_count(contest_id)
        if problem_count <= 0:
            return list()
        page = self.session.get(
            self.url + ConTestPath.GET_PROBLEM.format(contest_id)
        )

        soup = BeautifulSoup(page.text, "html.parser")
        table_element = soup.select("table")[1]
        tr_elements = table_element.select("tr")

        problem_data = list()
        for tr_element in tr_elements[1:]:
            td_elements = tr_element.select("td")
            problem_data.append({
                "id": td_elements[0].text.strip().replace("p", ""),
                "name": td_elements[1].text.strip() if td_elements[1].text.strip() == td_elements[2].text.strip() else td_elements[2].text.strip(),
            })
        
        return problem_data


    def get_contest_or_problem_information(self, contest_id, need_content=None):

        # get contest or problem information.
        # need_contest="contest", get the contest information.
        # need_contest="problem", get the problem information.

        page = self.session.get(
            self.url + ConTestPath.GET_SINGLE_EDIT.format(contest_id)
        )

        soup = BeautifulSoup(page.text, "html.parser")
        input_elements = soup.find_all("input")
        select_elements = soup.find_all("select")
        radio_elements = soup.find_all("div", class_="custom-control custom-radio")

        contest_problem_info_dict = dict()
        for input_elem in input_elements:
            if input_elem.get("name"):
                contest_problem_info_dict[input_elem.get("name")] = input_elem.get(
                    "value", ""
                )

        for select_elem in select_elements:
            if select_elem.get("name"):
                selected_option = select_elem.find("option", selected=True)
                selected_value = selected_option.get("value") if selected_option else ""
                contest_problem_info_dict[select_elem.get("name")] = selected_value

        for radio_elem in radio_elements:
            input_elem = radio_elem.find("input", checked=True)
            if input_elem:
                name = input_elem.get("name")
                value = input_elem.get("value")
                contest_problem_info_dict[name] = value

        contest_problem_info_dict["contest[save]"] = ""

        if need_content == "contest":
            contest_problem_info_dict = {
                key: value
                for key, value in contest_problem_info_dict.items()
                if "problems" not in key
            }

        if need_content == "problem":
            contest_problem_info_dict = {
                key: value
                for key, value in contest_problem_info_dict.items()
                if "problems" in key
            }

        return contest_problem_info_dict

    def contest_problem_upload(self, contest_id, problem_data):

        if "contest[save]" not in problem_data:
            problem_data.update({"contest[save]": ""})

        if "contest[teams][]" in problem_data:
            del problem_data["contest[teams][]"]
        
        if "contest[teamCategories][]" in problem_data:
            del problem_data["contest[teamCategories][]"]

        page = self.session.post(
            self.url + ConTestPath.POST_SINGLE.format(contest_id),
            data=problem_data,
        )

        return self.misjudgment(page)

    def get_testcases_all(self, problem_id):
        page = self.session.get(self.url + TestCasePath.GET.format(problem_id))
        soup = BeautifulSoup(page.text, "html.parser")
        rows = soup.select("table tr")

        testcases_dict = {}

        for row in range(1, len(rows)):
            href = rows[row].select("td")[0].select_one("a").get("href")
            if "delete_testcase" in href:
                id = href.split("/")[3]

            row_id = rows[row].select(".testrank")
            md5 = rows[row].select(".md5")

            file_md5 = md5[0].text.replace("\n", "").replace(" ", "")

            if row_id:
                file_id = row_id[0].text.replace("\n", "").replace(" ", "")
                left_md5 = file_md5
            else:
                info = {"id": id, "file_id": file_id}

                testcase = TestCase(**info)
                file_md5 = left_md5 + file_md5
                testcases_dict[file_md5] = testcase

        return testcases_dict

    def get_testcase(self, problem_id, testcase_id):
        testcases = {}
        page = self.session.get(
            self.url + TestCasePath.GET_INPUT.format(problem_id, testcase_id)
        )
        soup = BeautifulSoup(page.text, "html.parser")
        testcases["in"] = soup.text

        page = self.session.get(
            self.url + TestCasePath.GET_OUTPUT.format(problem_id, testcase_id)
        )
        soup = BeautifulSoup(page.text, "html.parser")
        testcases["out"] = soup.text

        return testcases

    def update_testcase(self, form_data, id):
        self.session.get(self.url + TestCasePath.GET.format(id))
        page = self.session.post(
            self.url + TestCasePath.GET.format(id), files=form_data
        )

        if page.status_code == 200:
            return True

    def update_problem_information(self, data, files, id):
        self.session.get(self.url + ProblemPath.EDIT.format(id))

        page = self.session.post(
            self.url + ProblemPath.EDIT.format(id), data=data, files=files
        )

        return self.misjudgment(page)
        

    def delete_problem(self, request, id):
        page = self.session.post(self.url + ProblemPath.DELETE.format(id))
        result = self.misjudgment(page)

        if result:
            return messages.success(request, "刪除成功")
        else:
            return messages.error(request, "刪除失敗")

    def delete_contest_problem(self, contest_id, web_problem_id):
        page = self.session.post(
            self.url + ConTestPath.DELETE.format(contest_id, web_problem_id)
        )

        is_success = True
        if page.status_code == 404:
            is_success = False

        return is_success

    def delete_testcase(self, id):
        self.session.get(self.url + TestCasePath.DELETE.format(id))
