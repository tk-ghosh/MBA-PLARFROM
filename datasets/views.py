import logging
import traceback

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from googleapiclient.errors import HttpError

from .drive_utils import resolve_type_variant_folder, upload_file_to_drive
from .models import Dataset

logger = logging.getLogger(__name__)


@login_required
def admin_panel_view(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to access the admin panel.")
        return redirect('dashboard')

    datasets = Dataset.objects.order_by('file_type', 'variant', '-uploaded_at')
    existing_types = Dataset.objects.values_list('file_type', flat=True).distinct()
    existing_variants = Dataset.objects.values_list('variant', flat=True).distinct()

    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        file_type = request.POST.get('file_type', '').strip()
        variant = request.POST.get('variant', '').strip()
        description = request.POST.get('description', '').strip()

        if not file_type or not variant or uploaded_file is None:
            messages.error(
                request,
                'Upload failed: type, variant and a file are all required.',
            )
        else:
            try:
                folder_id = resolve_type_variant_folder(file_type, variant)
                drive_file = upload_file_to_drive(
                    uploaded_file.file,
                    uploaded_file.name,
                    uploaded_file.content_type or 'application/octet-stream',
                    folder_id,
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
                    file_type=file_type,
                    variant=variant,
                    description=description,
                    drive_file_id=drive_file['id'],
                    drive_file_name=drive_file['name'],
                    drive_folder_id=folder_id,
                    uploaded_by=request.user,
                )
                messages.success(request, f'"{uploaded_file.name}" uploaded successfully.')
        return redirect('admin_panel')

    context = {
        'datasets': datasets,
        'existing_types': existing_types,
        'existing_variants': existing_variants,
    }
    return render(request, 'datasets/admin_panel.html', context)


@login_required
def dataset_list_view(request):
    datasets = Dataset.objects.order_by('file_type', 'variant', '-uploaded_at')
    return render(request, 'datasets/dataset_list.html', {'datasets': datasets})