from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

DEFAULT_API_DOC_TYPE = "swagger"
DEFAULT_API_DOC_URL = f"api:{DEFAULT_API_DOC_TYPE}"

SchemaView = get_schema_view(
    openapi.Info(
        title="API Documents",
        default_version="v1",
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    authentication_classes=(TokenAuthentication, SessionAuthentication),
    permission_classes=(IsAuthenticated,),
)
