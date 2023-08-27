from django.contrib import admin

from app.domservers.models import DomServerClient

# Register your models here.


@admin.register(DomServerClient)
class DomServerAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "host",
        "username",
        # "mask_password",
        "disable_ssl",
        "timeout",
        "category_id",
        "affiliation_id",
        "affiliation_country",
        "owner",
        "version",
        "api_version",
    ]
    # autocomplete_fields = ["party"]
