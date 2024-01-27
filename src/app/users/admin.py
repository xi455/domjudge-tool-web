from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from django_object_actions import DjangoObjectActions
from rest_framework.authtoken.admin import TokenAdmin, TokenProxy

from app.users.models import User
from utils.admins import action_display


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    def get_queryset(self, request):
        queryset = super().get_queryset(request)  # type: User.objects
        if not request.user.is_superuser:
            queryset = queryset.filter(username=request.user.username)
        return queryset

    def get_fieldsets(self, request, obj=None):
        user = request.user
        if not user.is_superuser and obj:
            return (
                (
                    None,
                    {
                        "fields": ("username", "password"),
                    },
                ),
                (
                    _("Personal info"),
                    {
                        "fields": ("first_name", "last_name", "email"),
                    },
                ),
            )

        return super().get_fieldsets(request, obj)


class APITokenAdmin(DjangoObjectActions, TokenAdmin):
    list_display = ("key", "token_header", "created", "user")
    list_display_links = ("user",)
    changelist_actions = ("make_token",)

    @action_display(
        label="建立 Token",
        description="建立 API Token",
        attrs={
            "class": "btn btn-outline-success",
        },
    )
    def make_token(self, request, queryset):
        TokenProxy.objects.create(user=request.user)

    @admin.display(description="API Authorization Header")
    def token_header(self, obj):
        return f"token {obj.key}"

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_queryset(self, request):
        queryset = super().get_queryset(request)  # type: User.objects
        if not request.user.is_superuser:
            queryset = queryset.filter(user=request.user)
        return queryset


admin.site.unregister(TokenProxy)
admin.site.register(TokenProxy, APITokenAdmin)
