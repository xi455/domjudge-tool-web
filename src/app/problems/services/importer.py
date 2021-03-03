import yaml
import shutil
import os

from pathlib import Path
from io import StringIO, BytesIO

from django.core.files.storage import FileSystemStorage

from ..models import Problem

file_storage = FileSystemStorage(location='/tmp/problems')


def remove_folder(instance: Problem):
    _id = str(instance.id).replace('-', '')
    if Path(f'/tmp/problems/problem_{_id}').exists():
        shutil.rmtree(f'/tmp/problems/problem_{_id}')


def copy_pdf(instance: Problem):
    _id = str(instance.id).replace('-', '')
    file_storage.save(f'problem_{_id}/problem.pdf', instance.description_file.file)


def create_problem_yaml(instance: Problem):
    _id = str(instance.id).replace('-', '')
    temp = StringIO(yaml.dump({'name': instance.name}, allow_unicode=True))
    file_storage.save(f'problem_{_id}/problem.yaml', temp)
    temp.seek(0)


def create_problem_time_limit(instance: Problem):
    content = StringIO(
        f"timelimit='{int(instance.time_limit)}'"
    )
    _id = str(instance.id).replace('-', '')
    file_storage.save(f'problem_{_id}/domjudge-problem.ini', content)


WINDOWS_LINE_ENDING = b'\r\n'
UNIX_LINE_ENDING = b'\n'


def create_in_out_text(instance: Problem):
    _id = str(instance.id).replace('-', '')
    for index, item in enumerate(instance.int_out_data.all()):
        num = index + 1
        input_content_b = item.input_content.\
            encode().\
            replace(WINDOWS_LINE_ENDING, UNIX_LINE_ENDING)
        file_storage.save(
            f'problem_{_id}/data/secret/{num}.in',
            BytesIO(input_content_b)
        )
        answer_content_b = item.answer_content.\
            encode().\
            replace(WINDOWS_LINE_ENDING, UNIX_LINE_ENDING)
        file_storage.save(
            f'problem_{_id}/data/secret/{num}.ans',
            BytesIO(answer_content_b)
        )


def create_problem_zip(instance: Problem):
    _id = str(instance.id).replace('-', '')
    zip_file_name = f'{instance.short_name}'
    path_root = '/tmp/problems'
    folder_name = f'problem_{_id}'
    out = shutil.make_archive(
        os.path.join(path_root, zip_file_name),
        'zip',
        root_dir=os.path.join(path_root, folder_name),
    )
    path = os.path.join(path_root, out)
    return path
