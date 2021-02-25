import yaml
import shutil
import os

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings

from ..models import Problem


def create_problem_yaml(instance: Problem):
    problem_yaml = ContentFile(
        yaml.dump({'name': instance.name}).encode(),
    )
    _id = str(instance.id).replace('-', '')
    default_storage.save(f'problem_{_id}/problem.yaml', problem_yaml)


def create_problem_time_limit(instance: Problem):
    content = ContentFile(
        f"timelimit='{int(instance.time_limit)}'"
    )
    _id = str(instance.id).replace('-', '')
    default_storage.save(f'problem_{_id}/domjudge-problem.ini', content)


def create_in_out_text(instance: Problem):
    _id = str(instance.id).replace('-', '')
    for index, item in enumerate(instance.int_out_data.all()):
        num = index + 1
        default_storage.save(
            f'problem_{_id}/data/secret/{num}.in',
            ContentFile(item.input_content.encode())
        )
        default_storage.save(
            f'problem_{_id}/data/secret/{num}.ans',
            ContentFile(item.answer_content.encode())
        )


def create_problem_zip(instance: Problem):
    _id = str(instance.id).replace('-', '')
    zip_file_name = f'{instance.short_name}'
    path_root = settings.MEDIA_ROOT
    out = shutil.make_archive(
        zip_file_name,
        'zip',
        os.path.join(path_root, f'problem_{_id}'),
    )
    path = os.path.join(path_root, out)
    print(os.path.join(path_root, f'problem_{_id}'))
    return path
