from django.contrib import admin
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe

from .models import Problem, ProblemInOut


class ProblemInOutInline(admin.TabularInline):
    model = ProblemInOut
    max_num = 10
    extra = 1


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'time_limit',
        'owner',
        'id',
        'make_zip',
    )
    list_filter = ('create_at', 'update_at')
    search_fields = ('name', )
    inlines = [ProblemInOutInline]
    readonly_fields = ('id', 'owner')
    fieldsets = (
        (None, {
            'fields': ('id', 'owner'),
        }),
        (
            '題目資訊',
            {
                'fields': (
                    'name',
                    'short_name',
                    'description_file',
                    'time_limit',
                ),
            },
        ),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(owner=request.user)
        return queryset

    def make_zip(self, obj, **kwargs):
        url = reverse_lazy('problem:zip', kwargs={'pk': str(obj.id)})
        return mark_safe(f'<a href="{url}">下載 zip</a>')

    make_zip.short_description = '下載壓縮檔'  # type: ignore

    def save_model(self, request, obj, form, change):
        if not obj.owner_id:
            obj.owner = request.user
        super().save_model(request, obj, form, change)
