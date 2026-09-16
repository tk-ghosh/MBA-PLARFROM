import logging
import re
import secrets
import traceback

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import render

from datasets.drive_utils import download_file_from_drive
from datasets.models import Dataset
from . import plan_to_upload

logger = logging.getLogger(__name__)

XLS_CONTENT_TYPE = 'application/vnd.ms-excel'


def _converter_context():
    datasets = Dataset.objects.order_by('-uploaded_at')
    datasets_json = {
        str(d.id): {
            'name': d.name,
            'category': d.category,
            'description': d.description,
        }
        for d in datasets
    }
    return {'datasets': datasets, 'datasets_json': datasets_json}


def _sanitize_filename(name):
    clean = re.sub(r'[^\w\s\-]', '', name or '')
    clean = ' '.join(clean.split())
    return clean.strip()


@login_required
def upload_converter_view(request):
    context = _converter_context()

    if request.method == 'POST':
        brand_name = request.POST.get('brand_name', '').strip() or 'PA CBHO'
        discount_rate = request.POST.get('discount_rate', '15') or '15'
        media_ac = request.POST.get('media_ac', '2') or '2'
        vat_rate = request.POST.get('vat_rate', '15') or '15'
        io_number = request.POST.get('io_number', '82009537') or '82009537'

        dataset_id = request.POST.get('dataset', '')
        uploaded_file = request.FILES.get('file')

        if dataset_id:
            try:
                dataset = Dataset.objects.get(pk=dataset_id)
                plan_source = download_file_from_drive(dataset.drive_file_id)
            except Exception:
                print(traceback.format_exc())
                logger.exception('Drive download failed for dataset %r', dataset_id)
                context['error'] = (
                    "Couldn't fetch that dataset from Google Drive. "
                    'Please try again or upload a file directly instead.'
                )
                return render(request, 'tools/upload_converter.html', context)
        elif uploaded_file:
            plan_source = uploaded_file
        else:
            context['error'] = 'Select a dataset or upload a file to convert.'
            return render(request, 'tools/upload_converter.html', context)

        try:
            df = plan_to_upload.build_upload_df(
                plan_path=plan_source,
                brand_name=brand_name,
                discount_rate=float(discount_rate) if discount_rate else 15,
                media_ac=float(media_ac) if media_ac else 2,
                vat_rate=float(vat_rate) if vat_rate else 15,
                io_number=int(io_number) if io_number else 82009537,
            )

            generated_total = int(df['Sum'].sum())

            plan_source.seek(0)
            plan_total = int(plan_to_upload.get_plan_total_spots(plan_source))
            is_match = (generated_total == plan_total)
        except Exception:
            print(traceback.format_exc())
            logger.exception('Plan->upload conversion failed')
            context['error'] = (
                "Couldn't process this file — make sure it's a TV Plan Excel file "
                "with a 'Plan' sheet in the expected format."
            )
            return render(request, 'tools/upload_converter.html', context)

        output_df = df.drop(columns=['Sum'])
        xls_buffer = plan_to_upload.dataframe_to_formatted_xls(output_df)
        xls_bytes = xls_buffer.getvalue()

        custom_name = _sanitize_filename(request.POST.get('output_filename', ''))
        if custom_name:
            filename = f'{custom_name}.xls'
        else:
            filename = f'upload_output_{brand_name}.xls'
        token = secrets.token_urlsafe(32)
        cache.set(token, {'bytes': xls_bytes, 'filename': filename}, timeout=600)

        result_context = _converter_context()
        result_context['result'] = {
            'generated_total': generated_total,
            'plan_total': plan_total,
            'is_match': is_match,
            'download_token': token,
        }
        return render(request, 'tools/upload_converter.html', result_context)

    return render(request, 'tools/upload_converter.html', context)


@login_required
def download_generated_file(request, token):
    payload = cache.get(token)
    if not payload:
        context = _converter_context()
        context['error'] = (
            "That download is no longer available (the file expires after 10 "
            'minutes or was never generated). Please run the conversion again.'
        )
        return render(request, 'tools/upload_converter.html', context)

    response = HttpResponse(payload['bytes'], content_type=XLS_CONTENT_TYPE)
    response['Content-Disposition'] = f'attachment; filename="{payload["filename"]}"'
    return response