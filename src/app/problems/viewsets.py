from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.decorators import action

from app.problems.models import Problem
from app.problems.serializers import ProblemSerializer
from app.problems.services.importer import build_zip_response


class ProblemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Problem.objects.all()
    serializer_class = ProblemSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(owner=self.request.user)

    @swagger_auto_schema(
        operation_description="Download problem zip file.",
        responses={
            "200": openapi.Response(
                "File Attachment",
                schema=openapi.Schema(type=openapi.TYPE_FILE),
            ),
        },
    )
    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, pk=None):
        obj = self.get_object()
        response = build_zip_response(obj)
        return response
