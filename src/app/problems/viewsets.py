from app.problems.models import Problem
from app.problems.serializers import ProblemSerializer

from rest_framework import viewsets
from rest_framework.decorators import action

from app.problems.services.importer import build_zip_response


class ProblemViewSet(viewsets.ModelViewSet):
    queryset = Problem.objects.all()
    serializer_class = ProblemSerializer

    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        obj = self.get_object()
        response = build_zip_response(obj)
        return response
