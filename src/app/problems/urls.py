from django.urls import path

from app.problems.views import allocate as problem_views

app_name = "problems"

urlpatterns = [
    path("zip/<uuid:pk>/", problem_views.get_zip, name="zip"),
    path("zip/upload/", problem_views.upload_zip_view, name="upload_zip"),
    path("zip/upload/<pk>", problem_views.upload_zip_view, name="upload_zip_with_pk"),
    path("zip/check/<uuid:pk>/", problem_views.check_zip_view, name="check_zip"),
    path("upload/", problem_views.problem_upload_view, name="problem_upload"),
]
