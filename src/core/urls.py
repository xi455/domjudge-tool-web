"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from app.users import views as user_views
from core.docs import DEFAULT_API_DOC_URL, SchemaView

apipatterns = [
    path("problem/", include("app.problems.apiurls")),
]

api_urlpatterns = [
    path("swagger/", SchemaView.with_ui(), name="swagger"),
    path("redoc/", SchemaView.with_ui(renderer="redoc"), name="redoc"),
    path("docs/", RedirectView.as_view(pattern_name=DEFAULT_API_DOC_URL), name="docs"),
    path("", include((apipatterns, "apis"))),
]

urlpatterns = [
    path("api/", include((api_urlpatterns, "api"))),
    path("admin/register/", user_views.register, name="register"),
    path("admin/", admin.site.urls),
    path("problem/", include("app.problems.urls", namespace="problem")),
    path("", RedirectView.as_view(pattern_name="admin:index")),
]
