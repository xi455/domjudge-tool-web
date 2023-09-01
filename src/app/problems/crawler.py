import requests

from bs4 import BeautifulSoup
from pydantic import BaseModel

import app.problems.exceptions as exceptions

# from src.core.settings import DOMSERVER_URL, DOMSERVER_USERNAME, DOMSERVER_PASSWORD


class TestCase(BaseModel):
    id: str
    file_id: str


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
        page = session.get(self.url + "login")
        soup = BeautifulSoup(page.text, "html.parser")
        data = {ele.get("name"): ele.get("value") for ele in soup.select("input")}
        data["_username"] = self.username
        data["_password"] = self.password

        response = session.post(self.url + "login", data=data)

        if response.url == self.url + "jury":
            return session

        raise exceptions.ProblemDownloaderLoginException("登入失敗")

    def request_contest_id(self, contests):
        if self.session:
            page = self.session.get(self.url + "jury/problems")
            soup = BeautifulSoup(page.text, "html.parser")

            contest_options = soup.select("option")
            if contests != "":
                for index in range(1, len(contest_options)):
                    option = contest_options[index].text.split(" - ")[-1]

                    if option == contests:
                        contest_id = int(contest_options[index].get("value"))
                        return contest_id

    def request_upload(self, files, contests):
        if self.session:
            contest_id = self.request_contest_id(contests)
            print(contest_id)
            data = {
                "problem_upload_multiple[contest]": contest_id,
            }
            problem_name_list = []
            for file_name in files:
                problem_name_list.append(file_name[1][0])

            print(data)
            page = self.session.post(self.url + "jury/problems", data=data, files=files)
            # page = self.session.get("https://lab-judge.ntub.tw/jury/problems")
            soup = BeautifulSoup(page.text, "html.parser")
            alert = soup.select_one(".alert-dismissible").get("class")

            if "alert-info" in alert:
                response = True
            else:
                response = False

            page = self.session.get(self.url + "jury/problems")
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

            return response, problem_id_list, contest_id

    def request_contest_problem_count(self, contest):
        if self.session:
            contest = self.request_contest_id(contests=contest)
            page = self.session.get(self.url + f"jury/contests/{contest}/edit")

            soup = BeautifulSoup(page.text, "html.parser")

            thead_elements = soup.select(".table thead")

            tbody = ""
            for thead in thead_elements:
                tbody = thead.find_next_sibling("tbody")
            if tbody:
                tr_elements_length = len(tbody.select("tr"))

                return tr_elements_length

    def request_contest_upload(self, contest, problem_data):
        if self.session:
            contest = self.request_contest_id(contests=contest)
            print(contest)
            page = self.session.get(self.url + f"jury/contests/{contest}/edit")

            soup = BeautifulSoup(page.text, "html.parser")
            # 創建一個空字典來存放 data
            data = {}

            # 找到所有的 input 和 select 元素
            input_elements = soup.find_all("input")
            select_elements = soup.find_all("select")

            # 找到所有的 custom-radio 元素
            radio_elements = soup.find_all("div", class_="custom-control custom-radio")

            # 遍歷 input 元素並生成 form-data
            for input_elem in input_elements:
                if input_elem.get("name"):
                    data[input_elem.get("name")] = input_elem.get("value", "")

            # 遍歷 select 元素並生成 form-data
            for select_elem in select_elements:
                if select_elem.get("name"):
                    selected_option = select_elem.find("option", selected=True)
                    selected_value = selected_option.get("value") if selected_option else ""
                    data[select_elem.get("name")] = selected_value

            # 遍歷 custom-radio 元素並找到被選中的 radio 值
            for radio_elem in radio_elements:
                input_elem = radio_elem.find("input", checked=True)
                if input_elem:
                    name = input_elem.get("name")
                    value = input_elem.get("value")
                    data[name] = value

            del data["contest[teams][]"]
            del data["contest[teamCategories][]"]

            data.update(problem_data)
            data["contest[save]"]: ""
            # print(data)
            page = self.session.post(
                self.url + f"jury/contests/{contest}/edit", data=data
            )

            soup = BeautifulSoup(page.text, "html.parser")
            error_elements = soup.select_one(".form-error-message")

            if error_elements:
                response = False
            else:
                response = True

            return response
    def request_contests_get_all(self):
        if self.session:
            url = self.url + "api/v4/contests?strict=false"
            # 發送 GET 請求
            response = requests.get(url)
            data = response.json()  # 將返回的 JSON 資料轉換為 Python 字典或列表

            return data

    def request_testcases_get_all(self, problem_id):
        if self.session:
            page = self.session.get(self.url + f"jury/problems/{problem_id}/testcases")
            soup = BeautifulSoup(page.text, "html.parser")
            rows = soup.select("table tr")

            testcases_dict = {}

            for row in range(1, len(rows)):
                href = rows[row].select("td")[0].select_one("a").get("href")
                if "delete_testcase" in href:
                    id = href.split("/")[3]

                row_id = rows[row].select(".testrank")
                name = rows[row].select(".filename")
                md5 = rows[row].select(".md5")

                file_md5 = md5[0].text.replace("\n", "").replace(" ", "")
                file_name = name[0].text.replace("\n", "").replace(" ", "")

                if row_id:
                    file_id = row_id[0].text.replace("\n", "").replace(" ", "")
                    left_md5 = file_md5
                else:
                    info = {"id": id, "file_id": file_id}

                    testcase = TestCase(**info)
                    file_md5 = left_md5 + file_md5
                    testcases_dict[file_md5] = testcase

            return testcases_dict

    def request_testcase_get(self, problem_id, testcase_id):
        if self.session:
            testcases = {}
            page = self.session.get(
                self.url
                + f"jury/problems/{problem_id}/testcases/{testcase_id}/fetch/input"
            )
            soup = BeautifulSoup(page.text, "html.parser")
            testcases["in"] = soup.text

            page = self.session.get(
                self.url
                + f"jury/problems/{problem_id}/testcases/{testcase_id}/fetch/output"
            )
            soup = BeautifulSoup(page.text, "html.parser")
            testcases["out"] = soup.text

            return testcases

    def request_update(self, form_data, id):
        if self.session:
            page = self.session.get(self.url + f"jury/problems/{id}/testcases")
            page = self.session.post(
                self.url + f"jury/problems/{id}/testcases", files=form_data
            )

    def request_problem_info_update(self, data, files, id):
        if self.session:
            page = self.session.get(self.url + f"jury/problems/{id}/edit")

            page = self.session.post(
                self.url + f"jury/problems/{id}/edit", data=data, files=files
            )

    def request_delete(self, id):
        if self.session:
            page = self.session.get(self.url + f"jury/problems/{id}/delete_testcase")
