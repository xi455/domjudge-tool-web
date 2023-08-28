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

    def request_upload(self, files, contests):
        if self.session:
            page = self.session.get(self.url + "jury/problems")
            soup = BeautifulSoup(page.text, "html.parser")

            contest_id = ""
            contest_options = soup.select("option")
            if contests != "":
                for index in range(1, len(contest_options)):
                    option = contest_options[index].text.split(" - ")[-1]

                    if option == contests:
                        contest_id = int(contest_options[index].get("value"))
                        # print(contest_options[index].text)
                        break

            data = {
                "problem_upload_multiple[contest]": contest_id,
            }
            problem_name_list = []
            for file_name in files:
                problem_name_list.append(file_name[1][0])

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

            if contest_id == "":
                option = "Do not link to a contest"

            return response, problem_id_list, option

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
