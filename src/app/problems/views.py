import os
from io import StringIO

from wsgiref.util import FileWrapper

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET

from .models import Problem
from .services.importer import (
    create_problem_yaml,
    create_in_out_text,
    create_problem_time_limit,
    create_problem_zip,
)


@require_GET
@login_required(login_url='/admin/login/')
@user_passes_test(lambda user: user.is_staff)
def get_zip(request, pk):
    obj = get_object_or_404(Problem, **{'pk': pk})
    create_problem_yaml(obj)
    create_in_out_text(obj)
    create_problem_time_limit(obj)
    zip_path = create_problem_zip(obj)
    temp = StringIO()
    file_name = os.path.basename(zip_path)
    response = StreamingHttpResponse(FileWrapper(temp), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'
    response['Content-Length'] = temp.tell()
    temp.seek(0)

    return response
