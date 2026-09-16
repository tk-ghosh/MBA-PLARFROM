import logging
import traceback

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from googleapiclient.errors import HttpError

from .drive_utils import upload_file_to_drive
from .models import Dataset

logger = logging.getLogger(__name__)


@login_required
def admin_panel_view(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access the admin panel.")
        return redirect('dashboard')

    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        name = request.POST.get('name', '').strip()
        category = request.POST.get('category', '').strip()
        description = request.POST.get('description', '').strip()

        if not name or not category or uploaded_file is None:
            messages.error(
                request,
                'Upload failed: name, category and a file are all required.',
            )
        else:
            try:
                drive_file = upload_file_to_drive(
                    uploaded_file.file,
                    uploaded_file.name,
                    uploaded_file.content_type or 'application/octet-stream',
                )
            except HttpError as exc:
                print(traceback.format_exc())
                logger.exception('Google Drive API rejected upload of %r', uploaded_file.name)
                hint = ''
                if 'storageQuotaExceeded' in str(exc) or 'do not have storage quota' in str(exc):
                    hint = (' Fix: upload into a Shared Drive folder on Google Drive '
                            '(add the service account as a Content Manager member), '
                            'or set up domain-wide delegation for a real user account.')
                messages.error(
                    request,
                    f'Google rejected this upload — {exc.reason or "see logs"}. No record was created.{hint}',
                )
            except Exception:
                print(traceback.format_exc())
                logger.exception('Google Drive upload failed for %r', uploaded_file.name)
                messages.error(
                    request,
                    'Upload failed: could not reach Google Drive. No record was created.',
                )
            else:
                Dataset.objects.create(
                    name=name,
                    category=category,
                    description=description,
                    drive_file_id=drive_file['id'],
                    drive_file_name=drive_file['name'],
                    uploaded_by=request.user,
                )
                messages.success(request, f'"{name}" uploaded successfully.')
        return redirect('admin_panel')

    datasets = Dataset.objects.order_by('-uploaded_at')
    return render(request, 'datasets/admin_panel.html', {'datasets': datasets})


@login_required
def dataset_list_view(request):
    datasets = Dataset.objects.order_by('-uploaded_at')
    return render(request, 'datasets/dataset_list.html', {'datasets': datasets})