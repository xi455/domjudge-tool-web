from django.urls import path, include

from .views import get_zip


app_name = 'problems'

urlpatterns = [
    path('zip/<uuid:pk>', get_zip, name='zip'),
]
