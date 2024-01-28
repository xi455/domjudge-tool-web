import json

from datetime import datetime
from enum import Enum
from typing import Optional

import requests

from bs4 import BeautifulSoup
from pydantic import BaseModel, validator

import app.problems.exceptions as exceptions


class TestCase(BaseModel):
    id: str
    file_id: str


class ServerContest(BaseModel):
    conteset_name: str
    conteset_id: str


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
    GET_SINGLE = "/jury/contests/{}"
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

        raise exceptions.ProblemDownloaderLoginException("登入失敗")

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

    # def get_contest_yaml(self, constest_id):
    #     return self.session.get(self.url + ApiPath.CONTEST_YAML.format(constest_id))

    def get_contest_all_name(self):
        data = self.get_contest_all()

        return data.keys()

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
            contest_short_name = td_elements[1].text.strip()
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
            contests_detail_dict[contest_short_name] = contest_details

        # for key, value in contests_detail_dict.items():
        #     print(key, value)

        return contests_detail_dict

    def get_problems(self):

        # get domjudge all problem information return dict type
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

    def upload_problem(self, files, contest_id):

        data = {
            "problem_upload_multiple[contest]": contest_id,
        }

        problem_name_list = []
        for file_name in files:
            problem_name_list.append(file_name[1][0])

        page = self.session.post(self.url + ProblemPath.POST, data=data, files=files)
        soup = BeautifulSoup(page.text, "html.parser")
        alert = soup.select_one(".alert-dismissible").get("class")

        if "alert-info" in alert:
            is_succeed = True
        else:
            is_succeed = False

        page = self.session.get(self.url + ProblemPath.GET)
        soup = BeautifulSoup(page.text, "html.parser")

        problem_id_list = []
        td_elements = soup.select("table td")
        for td in td_elements:
            for name in problem_name_list:
                text = td.text.strip()

                if text == name:
                    problem_id_list.append(
                        td.select_one("a").get("href").split("/")[-1]
                    )

        return is_succeed, problem_id_list, contest_id

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
                "conteset_name": web_contest_name,
                "conteset_id": web_contest_id,
            }

            server_contest = ServerContest(**contest_info)
            server_contests_info_dict[web_contest_name] = server_contest

        return server_contests_info_dict

    def contest_and_problem_create(self, create_contest_information):

        # Post the contest area creation information and upload it to
        # domjudge to create a new contest area.

        # return the bool to see if it succeeded.

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

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
        print(page.text)

        if "Error" in page.text:
            print("the upload is ", False)
            return False
        else:
            print("the upload is ", True)
            return True

    def contest_problem_update(self, contest_id, contest_data_dict):

        # return the bool to see if it succeeded.

        problem_information_dict = self.get_contest_or_problem_information(
            contest_id=contest_id, need_content="problem"
        )
        contest_data_dict.update(problem_information_dict)

        contest_data_dict.update({"contest[save]": ""})

        page = self.session.post(
            self.url + ConTestPath.POST_SINGLE.format(contest_id),
            data=contest_data_dict,
        )

        if "Error" in page.text:
            return False
        else:
            return True

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
        contest_problem_info_dict = self.get_contest_or_problem_information(
            contest_id=contest_id
        )

        del contest_problem_info_dict["contest[teams][]"]
        del contest_problem_info_dict["contest[teamCategories][]"]

        contest_problem_info_dict.update(problem_data)

        for key, value in contest_problem_info_dict.items():
            print(key, value, type(value))

        page = self.session.post(
            self.url + ConTestPath.POST_SINGLE.format(contest_id),
            data=contest_problem_info_dict,
        )

        soup = BeautifulSoup(page.text, "html.parser")
        error_elements = soup.select_one(".form-error-message")

        return error_elements

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
        if page.status_code == 200:
            return True

    def delete_problem(self, id):
        self.session.post(self.url + ProblemPath.DELETE.format(id))

    def delete_contest_problem(self, contest_id, web_problem_id):
        page = self.session.post(
            self.url + ConTestPath.DELETE.format(contest_id, web_problem_id)
        )

        print(self.url + ConTestPath.DELETE.format(contest_id, web_problem_id))
        print(page.status_code)

        is_success = True
        if page.status_code == 404:
            is_success = False

        return is_success

    def delete_testcase(self, id):
        self.session.get(self.url + TestCasePath.DELETE.format(id))
