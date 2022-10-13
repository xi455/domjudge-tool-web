from django.urls import include, path
from rest_framework.routers import SimpleRouter

from app.problems.viewsets import ProblemViewSet

app_name = "problems"

router = SimpleRouter(trailing_slash=False)
router.register("problems", ProblemViewSet, "problems")

urlpatterns = [
    path("", include(router.urls)),
]
