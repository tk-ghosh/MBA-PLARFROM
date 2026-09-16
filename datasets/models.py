from django.conf import settings
from django.db import models


class Dataset(models.Model):
    file_type = models.CharField(max_length=100)
    variant = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    drive_file_id = models.CharField(max_length=200)
    drive_file_name = models.CharField(max_length=255)
    drive_folder_id = models.CharField(max_length=200, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.drive_file_name