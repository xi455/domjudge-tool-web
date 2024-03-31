from django.contrib import messages
from utils.admins import testcase_md5
from pydantic import BaseModel
from app.problems import exceptions as problem_exceptions

class ProblemTestCase(BaseModel):
    sample: bool
    input: str
    output: str

def handle_problem_testcase_data(problem_obj):
        """
        Handle the problem testcase data.

        Args:
            problem_obj (Problem): The problem object.

        Returns:
            dict: A dictionary containing the problem testcases.
        """
        problem_testcase_obj_all = problem_obj.int_out_data.all()

        problems_dict = dict()
        for testcase_obj in problem_testcase_obj_all:
            problem_testcase_md5 = testcase_md5(
                testcase_obj.input_content
            ) + testcase_md5(testcase_obj.answer_content)

            problem_testcase_info = {
                "sample": testcase_obj.is_sample,
                "input": testcase_obj.input_content,
                "output": testcase_obj.answer_content,
            }

            problem_testcase = ProblemTestCase(**problem_testcase_info)
            problems_dict[problem_testcase_md5] = problem_testcase

        return problems_dict

def handle_testcases_difference(web_testcases_all_dict, problems_dict):
    """
    Compares the testcases between the web_testcases_all_dict and problems_dict
    and returns the differences and intersections.

    Args:
        web_testcases_all_dict (dict): A dictionary containing the testcases from the web.
        problems_dict (dict): A dictionary containing the testcases from the problems.

    Returns:
        tuple: A tuple containing three sets:
            - web_testcases_difference: The testcases that are in web_testcases_all_dict but not in problems_dict.
            - web_testcases_retain: The testcases that are in both web_testcases_all_dict and problems_dict.
            - problems_testcases_difference: The testcases that are in problems_dict but not in web_testcases_all_dict.
    """
    web_testcases_md5 = set(web_testcases_all_dict.keys())
    problems_testcases_md5 = set(problems_dict.keys())

    problems_testcases_difference = problems_testcases_md5.difference(
        web_testcases_md5
    )
    web_testcases_difference = web_testcases_md5.difference(problems_testcases_md5)
    web_testcases_retain = set(web_testcases_md5).intersection(problems_testcases_md5)

    return web_testcases_difference, web_testcases_retain, problems_testcases_difference

def handle_testcases_delete(
    web_testcases_difference, web_testcases_all_dict, problem_crawler
):
    """
    Delete test cases from the problem crawler based on the given web_testcases_difference.

    Args:
        web_testcases_difference (list): List of MD5 hashes representing the test cases to be deleted.
        web_testcases_all_dict (dict): Dictionary containing testcase MD5 hashes as keys and corresponding input/output test cases as values.
        problem_crawler (ProblemCrawler): Object used to delete test cases.

    Returns:
        None
    """
    for web_md5 in web_testcases_difference:
        web_testcase_id = web_testcases_all_dict[web_md5].deleteid
        problem_crawler.delete_testcase(id=web_testcase_id)

def handle_exist_testcases_format(web_testcases_retain, web_testcases_all_dict, problems_dict):
    """
    Formats the existing test cases for a problem.

    Args:
        web_testcases_retain (list): A list of web test cases to retain.
        web_testcases_all_dict (dict): A dictionary containing all web test cases.
        problems_dict (dict): A dictionary containing problem information.

    Returns:
        tuple: A tuple containing two dictionaries:
            - problem_testcase_info_data: A dictionary containing the formatted input and output files for each test case.
            - sample_data: A dictionary containing the sample test cases.

    """
    problem_testcase_info_data = dict()
    sample_data = dict()
    for web_md5 in web_testcases_retain:
        testcase_in, testcase_out = (
            problems_dict[web_md5].input,
            problems_dict[web_md5].output,
        )

        problem_testcase_info_data.update({
            f"update_input[{web_testcases_all_dict[web_md5].id}]": ("update.in", testcase_in),
            f"update_output[{web_testcases_all_dict[web_md5].id}]": ("update.out", testcase_out),
        })

        if problems_dict[web_md5].sample:
            sample_data.update({
                f"sample[{web_testcases_all_dict[web_md5].id}]": "sample",
            })

    return problem_testcase_info_data, sample_data

def handle_web_add_testcases_format(problems_testcases_difference, problems_dict):
    """
    Handle the addition of testcases for a problem in a specific format.

    Args:
        problems_testcases_difference (str): The md5 index of the problem in the `problems_dict`.
        problems_dict (dict): A dictionary containing information about the problems.

    Returns:
        tuple: A tuple containing two dictionaries:
            - problem_testcase_info_data (dict): A dictionary containing information about the added testcases.
            - sample_data (dict): A dictionary containing information about the sample testcases.

    """
    problem_testcase_info_data = dict()
    sample_data = dict()
    testcase_in, testcase_out = (
        problems_dict[problems_testcases_difference].input,
        problems_dict[problems_testcases_difference].output,
    )
    problem_testcase_info_data.update({
        "add_input": ("add.in", testcase_in),
        "add_output": ("add.out", testcase_out),
    })

    if problems_dict[problems_testcases_difference].sample:
        sample_data.update({
            "add_sample": "on",
        })

    return problem_testcase_info_data, sample_data

def create_not_exist_testcases(problem_log_obj, web_testcases_all_dict, web_testcases_retain, problems_testcases_all_dict, problems_testcases_difference, problem_crawler):
    for problem_testcase in problems_testcases_difference:
        problem_testcase_info_data, sample_data = handle_exist_testcases_format(
            web_testcases_retain,
            web_testcases_all_dict,
            problems_dict=problems_testcases_all_dict,
        )
        add_problem_testcase_info_data, add_sample_data = handle_web_add_testcases_format(
            problems_testcases_difference=problem_testcase,
            problems_dict=problems_testcases_all_dict,
        )

        problem_testcase_info_data.update(add_problem_testcase_info_data)
        sample_data.update(add_sample_data)

        result = problem_crawler.create_testcase(
            form_data=problem_testcase_info_data,
            sample_data=sample_data,
            id=problem_log_obj.web_problem_id,
        )

        if not result:
            raise problem_exceptions.ProblemTestCaseUploadException("測資更新錯誤！！")
        
        web_testcases_all_dict = problem_crawler.get_testcases_all(
            problem_id=problem_log_obj.web_problem_id
        )

        (
            web_testcases_difference,
            web_testcases_retain,
            problems_testcases_difference,
        ) = handle_testcases_difference(
            web_testcases_all_dict=web_testcases_all_dict,
            problems_dict=problems_testcases_all_dict,
        )

def edit_exist_testcases(problem_log_obj, web_testcases_retain, web_testcases_all_dict, problems_testcases_all_dict, problem_crawler):
    problem_testcase_info_data, sample_data = handle_exist_testcases_format(
        web_testcases_retain,
        web_testcases_all_dict,
        problems_dict=problems_testcases_all_dict,
    )

    result = problem_crawler.create_testcase(
        form_data=problem_testcase_info_data,
        sample_data=sample_data,
        id=problem_log_obj.web_problem_id,
    )

    if not result:
        raise problem_exceptions.ProblemTestCaseUploadException("測資更新錯誤！！")
