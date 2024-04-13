import requests

from enum import Enum
from bs4 import BeautifulSoup

from app.problems import exceptions as problem_exceptions

from utils import exceptions as utils_exceptions
from utils import validator_pydantic as utils_validator_pydantic


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

        raise problem_exceptions.ProblemDownloaderLoginException("Login Error.")

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

        if "Error: problem.externalid:" in page.text:
            return False

        if error_elements and page.status_code in (400, 401, 403, 404, 500, 503):
            return False
        else:
            return True

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

            contest_details = utils_validator_pydantic.ContestInfo(**contest_info_dict)
            contests_detail_dict[contest_shortname] = contest_details

        return contests_detail_dict

    def get_problems(self):

        # get domjudge all problem information return class type
        # example: {problem_name: class(id=problem_id, name=problem_name)}

        page = self.session.get(self.url + ProblemPath.GET)
        soup = BeautifulSoup(page.text, "html.parser")

        result = self.misjudgment(page)
        if not result:
            return dict()

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

            problem_obj = utils_validator_pydantic.ProblemInfo(**problem_info)
            problem_data_dict[name] = problem_obj

        return problem_data_dict

    def upload_problem(self, files, contest_id):
        data = {
            "problem_upload_multiple[contest]": contest_id,
        }

        problem_name_list = []
        for index in range(len(files)):
            problem_name_list.append(files[index][2])
            files[index] = files[index][:-1]

        page = self.session.post(self.url + ProblemPath.POST, data=data, files=files)
        with open("/Users/hongchengxi/Documents/python_project/in.txt", "w", encoding="utf-8") as f:
            f.write(page.text)

        result = self.misjudgment(page)
        if result:
            is_succeed = True
        else:            
            message = "題目上傳失敗！！ 題目簡稱可能已與伺服器內題目重名。"
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
    
    def get_testcases(self, href):
        page = self.session.get(self.url + href)
        soup = BeautifulSoup(page.text, "html.parser")

        return soup.text

    def get_testcases_all(self, problem_id):
        page = self.session.get(self.url + TestCasePath.GET.format(problem_id))
        soup = BeautifulSoup(page.text, "html.parser")

        testcases_dict = dict()
        tr_elements = soup.select("table tr")
        for index in range(1, len(tr_elements), 2):
            testcase_data = dict()
            td_elements = tr_elements[index].select("td")

            for td in td_elements:
                href = td.select_one("a")
                if href:
                    href = href.get("href")
                    if "/delete_testcase" in href:
                        id = href.split("/")[3]
                        testcase_data["deleteid"] = id

                sample = td.select_one("input[type=checkbox]")
                if sample:
                    if sample.has_attr("checked"):
                        testcase_data["sample"] = "sample"
                    else:
                        testcase_data["sample"] = ""

                testcase_href = td.select_one("a")
                if testcase_href:
                    testcase_href = testcase_href.get("href")
                    if "/fetch/" in testcase_href:
                        testcase = self.get_testcases(testcase_href)
                        testcase_data["input"] = testcase

                        id = testcase_href.split("/")[5]
                        testcase_data["id"] = id

                if "class" in td.attrs:
                    if "md5" in td.attrs["class"]:
                        left_md5 = td.text.strip()

            td_elements = tr_elements[index + 1].select("td")
            for td in td_elements:
                testcase_href = td.select_one("a")
                if testcase_href:
                    testcase_href = testcase_href.get("href")
                    if "/fetch/" in testcase_href:
                        testcase = self.get_testcases(testcase_href)
                        testcase_data["output"] = testcase

                if "class" in td.attrs:
                    if "md5" in td.attrs["class"]:
                        right_md5 = td.text.strip()

            if left_md5 and right_md5:
                md5 = left_md5 + right_md5
                testcases_dict[md5] = utils_validator_pydantic.WebTestCase(**testcase_data)
        
        return testcases_dict

    def create_testcase(self, form_data, sample_data, id):
        self.session.get(self.url + TestCasePath.GET.format(id))
        page = self.session.post(
            self.url + TestCasePath.GET.format(id), files=form_data, data=sample_data
        )

        return self.misjudgment(page)

    def update_problem_information(self, data, files, id):
        self.session.get(self.url + ProblemPath.EDIT.format(id))

        page = self.session.post(
            self.url + ProblemPath.EDIT.format(id), data=data, files=files
        )

        return self.misjudgment(page)
    
    def delete_problem(self, id):
        page = self.session.post(self.url + ProblemPath.DELETE.format(id))

    def delete_contest_problem(self, contest_id, web_problem_id):
        page = self.session.post(
            self.url + ConTestPath.DELETE.format(contest_id, web_problem_id)
        )

        return self.misjudgment(page)

    def delete_testcase(self, id):
        self.session.get(self.url + TestCasePath.DELETE.format(id))