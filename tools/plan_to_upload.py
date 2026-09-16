"""
Plan -> Upload converter
=========================
Converts a Marico TV Plan (.xlsx, sheet 'Plan') into the system upload
format (Brand, ChannelName, Details, ProgramName, DiscountRate, Media_AC,
VatRate, Duration, GrossRatePerMinute, AIT, IO, PO, Month, [1]...[31]).
"""

import openpyxl
import pandas as pd
import xlwt
from datetime import datetime, time as dtime
from io import BytesIO


def _to_24h_hour(from_time_val):
    if from_time_val is None or from_time_val == '':
        return None
    if isinstance(from_time_val, datetime):
        return from_time_val.hour
    if isinstance(from_time_val, dtime):
        return from_time_val.hour
    s = str(from_time_val).strip().upper()
    try:
        hh_mm, ampm = s.split(' ')
        hour = int(hh_mm.split(':')[0])
        if ampm == 'PM' and hour != 12:
            hour += 12
        if ampm == 'AM' and hour == 12:
            hour = 0
        return hour
    except Exception:
        return None


def build_upload_df(
    plan_path,
    sheet_name='Plan',
    brand_name='PA CBHO',
    discount_rate=15,
    media_ac=2,
    vat_rate=15,
    io_number=82009537,
):
    wb = openpyxl.load_workbook(plan_path, data_only=True)
    ws = wb[sheet_name]

    header_row = 9
    data_start_row = 12

    date_cols = {}
    max_col_scan = ws.max_column
    for col in range(1, max_col_scan + 1):
        val = ws.cell(row=header_row, column=col).value
        if isinstance(val, datetime):
            date_cols[col] = val.date()

    base_rows = []
    for r in range(data_start_row, ws.max_row + 1):
        channel = ws.cell(row=r, column=1).value
        program_name = ws.cell(row=r, column=2).value
        day = ws.cell(row=r, column=7).value
        from_time = ws.cell(row=r, column=8).value
        position = ws.cell(row=r, column=12).value
        tvc_duration = ws.cell(row=r, column=16).value
        net_rate = ws.cell(row=r, column=19).value

        if not channel or not program_name:
            continue
        if not day or not from_time:
            continue
        if 'subtotal' in str(channel).lower() or 'subtotal' in str(program_name).lower():
            continue

        daily = {}
        for c, date in date_cols.items():
            v = ws.cell(row=r, column=c).value
            daily[date] = v if isinstance(v, (int, float)) else 0

        if sum(daily.values()) == 0:
            continue

        hour = _to_24h_hour(from_time)
        if hour is None:
            continue

        base_rows.append({
            'channel': channel,
            'details': f"{day} at {hour:02d}:00",
            'program_name': f"{program_name} in {position}",
            'duration': tvc_duration,
            'gross_rate': (net_rate / (1 - discount_rate / 100)) if net_rate else 0,
            'daily': daily,
        })

    all_months = sorted({d.month for br in base_rows for d in br['daily']})

    records = []
    for m in all_months:
        for br in base_rows:
            month_days = {d.day: v for d, v in br['daily'].items() if d.month == m}
            if sum(month_days.values()) == 0:
                continue
            row = {
                'Brand': brand_name,
                'ChannelName': br['channel'],
                'Details': br['details'],
                'ProgramName': br['program_name'],
                'DiscountRate': discount_rate,
                'Media_AC': media_ac,
                'VatRate': vat_rate,
                'Duration': br['duration'],
                'GrossRatePerMinute': br['gross_rate'],
                'AIT': None,
                'IO': io_number,
                'PO': None,
                'Month': m,
            }
            for day_num in range(1, 32):
                v = month_days.get(day_num, None)
                row[f'[{day_num}]'] = v if v else None
            row['Sum'] = sum(month_days.values())
            records.append(row)

    df = pd.DataFrame(records)
    return df


def get_plan_total_spots(plan_path, sheet_name='Plan', data_start_row=12):
    wb = openpyxl.load_workbook(plan_path, data_only=True)
    ws = wb[sheet_name]
    total = 0
    for r in range(data_start_row, ws.max_row + 1):
        channel = ws.cell(row=r, column=1).value
        program_name = ws.cell(row=r, column=2).value
        if not channel or not program_name:
            continue
        if 'subtotal' in str(channel).lower() or 'subtotal' in str(program_name).lower():
            continue
        val = ws.cell(row=r, column=17).value  # column Q = Total Spots
        if isinstance(val, (int, float)):
            total += val
    return total


def dataframe_to_formatted_xls(df):
    # Note: xlwt writes legacy Excel .xls files and has a 65,536-row limit
    # (old .xls format). Fine for current datasets (hundreds of rows), but
    # bear it in mind if a future dataset grows large enough to hit it.
    wb = xlwt.Workbook()
    ws = wb.add_sheet('Sheet1')

    header_style = xlwt.easyxf(
        'font: bold on; '
        'borders: left thin, right thin, top thin, bottom thin;'
    )
    data_style = xlwt.easyxf(
        'borders: left thin, right thin, top thin, bottom thin;'
    )

    for col_idx, col_name in enumerate(df.columns):
        ws.write(0, col_idx, col_name, header_style)

    for row_idx, row in enumerate(df.itertuples(index=False), start=1):
        for col_idx, value in enumerate(row):
            if value is None or (isinstance(value, float) and value != value):  # NaN check
                ws.write(row_idx, col_idx, None, data_style)
            else:
                ws.write(row_idx, col_idx, value, data_style)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer