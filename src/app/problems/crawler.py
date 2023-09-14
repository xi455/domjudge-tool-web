from enum import Enum
from bs4 import BeautifulSoup
from pydantic import BaseModel

import requests
import app.problems.exceptions as exceptions


class TestCase(BaseModel):
    id: str
    file_id: str


class ServerContest(BaseModel):
    conteset_name: str
    conteset_id: str


class HomePath(str, Enum):
    LOGIN = "/login"
    JURY = "/jury"


class ProblemPath(str, Enum):
    GET = "/jury/problems"
    ADD = "/jury/problems"
    EDIT = "/jury/problems/{}/edit"
    DELETE = "/jury/problems/{}/delete"


class ConTestPath(str, Enum):
    GET = "/jury/contests"
    EDIT = "/jury/contests/{}/edit"
    DELETE = "/jury/contests/{}/problems/{}/delete"


class TestCasePath(str, Enum):
    GET = "/jury/problems/{}/testcases"
    GET_INPUT = "/jury/problems/{}/testcases/{}/fetch/input"
    GET_OUTPUT = "/jury/problems/{}/testcases/{}/fetch/output"
    DELETE = "/jury/problems/{}/delete_testcase"


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

    def upload_problem(self, files, contest_id):

        data = {
            "problem_upload_multiple[contest]": contest_id,
        }

        problem_name_list = []
        for file_name in files:
            problem_name_list.append(file_name[1][0])

        page = self.session.post(self.url + ProblemPath.ADD, data=data, files=files)
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
        page = self.session.get(self.url + ConTestPath.EDIT.format(contest_id))
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

    def contest_problem_upload(self, contest_id, problem_data):
        page = self.session.get(self.url + ConTestPath.EDIT.format(contest_id))

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

        del contest_problem_info_dict["contest[teams][]"]
        del contest_problem_info_dict["contest[teamCategories][]"]

        contest_problem_info_dict.update(problem_data)
        contest_problem_info_dict["contest[save]"]: ""

        page = self.session.post(
            self.url + ConTestPath.EDIT.format(contest_id),
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

        is_success = True
        if page.status_code == 404:
            is_success = False

        return is_success

    def delete_testcase(self, id):
        self.session.get(self.url + TestCasePath.DELETE.format(id))
