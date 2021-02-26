import os

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET
from django.core.files import File

from .models import Problem
from .services.importer import (
    create_problem_yaml,
    create_in_out_text,
    create_problem_time_limit,
    create_problem_zip,
    copy_pdf,
    remove_folder,
)


@require_GET
@login_required(login_url='/admin/login/')
@user_passes_test(lambda user: user.is_staff)
def get_zip(request, pk):
    obj = get_object_or_404(Problem, pk=pk)
    remove_folder(obj)
    copy_pdf(obj)
    create_problem_yaml(obj)
    create_in_out_text(obj)
    create_problem_time_limit(obj)
    zip_path = create_problem_zip(obj)
    file = File(open(zip_path, 'rb'))
    file_name = os.path.basename(zip_path)
    response = StreamingHttpResponse(file, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'
    return response
