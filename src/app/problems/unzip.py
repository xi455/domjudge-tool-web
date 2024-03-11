import zipfile

from django.core.files.base import ContentFile

from app.users.models import User 
from app.problems.models import Problem
from app.problems.models import ProblemInOut

from app.problems import exceptions as problem_exceptions

def handle_upload_required_file(file):
    """
    Extracts information from a zip file and returns a dictionary containing the extracted data.

    Args:
        file (str): The zip file.

    Returns:
        dict: A dictionary containing the extracted information from the zip file. The dictionary has the following keys:
            - "problem_title": The title of the problem.
            - "time_limit": The time limit for the problem.
            - "problem_pdf": The contents of the problem PDF file.
            - "testcases_data": A dictionary containing the contents of the testcase files. The keys are the filenames and the values are the file contents.
    """
    try:
        with zipfile.ZipFile(file, 'r') as zip_ref:

            file_info_dict = {
                "problem_title": None,
                "time_limit": None,
                "problem_pdf": None,
                "testcases_data": None,
            }

            testcase_data = dict()
            for filename in zip_ref.namelist():
                if filename == "problem.yaml":
                    file_context = zip_ref.read(filename).decode("utf-8")
                    file_info_dict["problem_title"] = file_context.split(" ")[-1].strip()                
                
                if filename == "domjudge-problem.ini":
                    file_context = zip_ref.read(filename).decode("utf-8")                            
                    file_info_dict["time_limit"] = float(file_context.split("=")[-1][1:-1])

                if filename == "problem.pdf":
                    file_data = zip_ref.read(filename)
                    file_info_dict["problem_pdf"] = file_data                

                if filename.endswith(".ans") or filename.endswith(".in"):
                    file_data = zip_ref.read(filename).decode("utf-8")
                    testcase_data[filename] = file_data

            file_info_dict["testcases_data"] = testcase_data
            
            return file_info_dict

    except Exception:
        raise problem_exceptions.ContestCopyException(
            "File formatting errors!"
        )
        
    

def handle_unzip_problem_obj(file_info_dict):
    """
    Handles the unzipping of a problem object.

    Args:
        file_info_dict (dict): A dictionary containing information about the file.

    Returns:
        problem_obj: The created Problem object.
    """
    problem_obj = create_unzip_problem_obj(file_info_dict)
    format_data = handle_unzip_probleminout_data_format(file_info_dict)
    create_unzip_probleminout_obj(format_data, problem_obj)

    return problem_obj
    

def create_problem_pdf(file_info_dict):
    """
    Create a PDF file from the given file_info_dict.

    Args:
        file_info_dict (dict): A dictionary containing the information about the PDF file.
            It should have the following keys:
            - "problem_title": The title of the problem.
            - "problem_pdf": The content of the PDF file.

    Returns:
        ContentFile: The created PDF file.

    """
    pdf_name = file_info_dict["problem_title"] + ".pdf"
    pdf_content = file_info_dict["problem_pdf"]
    pdf_file = ContentFile(pdf_content, name=pdf_name)

    return pdf_file


def create_unzip_problem_obj(file_info_dict):
    """
    Create and return a Problem object based on the provided file information dictionary.

    Args:
        file_info_dict (dict): A dictionary containing information about the problem file.

    Returns:
        Problem: The created Problem object.

    """
    pdf_file = create_problem_pdf(file_info_dict)
    problem_obj = Problem.objects.create(
        name=file_info_dict["problem_title"],
        description_file=pdf_file,
        time_limit=file_info_dict["time_limit"],
        owner=User.objects.get(username="admin"),
        is_processed=True,
    )
    return problem_obj


def create_unzip_probleminout_obj(format_data, problem_obj):
    """
    Create ProblemInOut objects based on the given format_data and problem_obj.

    Args:
        format_data (dict): A dictionary containing the format data.
        problem_obj: The problem object to associate the ProblemInOut objects with.

    Returns:
        None
    """
    for key, value in format_data.items():
        ProblemInOut.objects.create(
            problem=problem_obj,
            is_sample=True if value["state"] == "sample" else False,
            input_content=value["in"],
            answer_content=value["ans"],
        )


def handle_unzip_probleminout_data_format(file_info_dict):
    """
    Formats the testcase data obtained from the file_info_dict dictionary.

    Args:
        file_info_dict (dict): A dictionary containing the testcase data.

    Returns:
        dict: A formatted dictionary containing the testcase data.

    """
    testcase_data = file_info_dict["testcases_data"]
    formatted_data = dict()

    for filename, file_data in testcase_data.items():
        file_name, file_extension = filename.split(".")
        file_name = file_name.split("/")
        file_state, file_name = file_name[-2], file_name[-1]
        file_key = f"{file_state}/{file_name}"

        if file_key not in formatted_data:
            formatted_data[file_key] = {"state": file_state, "in": None, "ans": None}
            
            if file_extension == "in":
                formatted_data[file_key]["in"] = file_data
            
            if file_extension == "ans":
                formatted_data[file_key]["ans"] = file_data

        else:
            if file_extension == "in":
                formatted_data[file_key]["in"] = file_data
            
            if file_extension == "ans":
                formatted_data[file_key]["ans"] = file_data

    return formatted_data