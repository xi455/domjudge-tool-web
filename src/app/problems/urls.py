from django.urls import path

from .views import get_zip, upload_zip_view

app_name = "problems"

urlpatterns = [
    path("zip/<uuid:pk>/", get_zip, name="zip"),
    path("zip/upload/", upload_zip_view, name="upload_zip"),
]
