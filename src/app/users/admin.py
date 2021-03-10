from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from app.users.models import User


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
                (None, {
                    'fields': ('username', 'password'),
                }),
                (
                    _('Personal info'),
                    {
                        'fields': ('first_name', 'last_name', 'email'),
                    },
                ),
            )

        return super().get_fieldsets(request, obj)
