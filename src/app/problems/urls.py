from django.urls import path

from .views import get_zip, upload_zip_view, check_zip_view

app_name = "problems"

urlpatterns = [
    path("zip/<uuid:pk>/", get_zip, name="zip"),
    path("zip/upload/", upload_zip_view, name="upload_zip"),
    path("zip/upload/<pk>", upload_zip_view, name="upload_zip_with_pk"),
    path("zip/check/<uuid:pk>/", check_zip_view, name="check_zip"),
]
