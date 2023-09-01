from django.urls import path

from .views import get_zip, problem_view

app_name = "problems"

urlpatterns = [
    path("zip/<uuid:pk>/", get_zip, name="zip"),
    # path("upload/", upload_view, name="upload"),
    # path("upload/<uuid:pk>/", upload, name="upload"),
]
