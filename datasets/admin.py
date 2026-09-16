from django.contrib import admin

from .models import Dataset


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'drive_file_name', 'uploaded_by', 'uploaded_at')
    list_filter = ('category', 'uploaded_at')
    search_fields = ('name', 'category', 'drive_file_name')
    readonly_fields = ('drive_file_id', 'drive_file_name', 'uploaded_at')