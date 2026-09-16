from django.contrib import admin

from .models import Dataset


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ('drive_file_name', 'file_type', 'variant', 'uploaded_by', 'uploaded_at')
    list_filter = ('file_type', 'variant', 'uploaded_at')
    search_fields = ('drive_file_name', 'file_type', 'variant')
    readonly_fields = ('drive_file_id', 'drive_file_name', 'drive_folder_id', 'uploaded_at')