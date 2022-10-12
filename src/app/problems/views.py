from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET

from .models import Problem
from .services.importer import build_zip_response


@require_GET
@login_required(login_url='/admin/login/')
@user_passes_test(lambda user: user.is_staff)
def get_zip(request, pk):
    obj = get_object_or_404(Problem, pk=pk)
    response = build_zip_response(obj)
    return response
