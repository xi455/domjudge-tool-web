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
        'make_zip'
    )
    list_filter = ('create_at', 'update_at')
    search_fields = ('name',)
    inlines = [ProblemInOutInline]

    def make_zip(self, obj, **kwargs):
        url = reverse_lazy('problem:zip', kwargs={'pk': str(obj.id)})
        return mark_safe(f'<a href="{url}">下載 zip</a>')

    make_zip.short_description = "下載壓縮檔"



