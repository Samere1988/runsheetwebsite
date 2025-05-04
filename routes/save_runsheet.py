import openpyxl
from openpyxl.styles import Alignment, Border, Side, Font
from openpyxl.utils import get_column_letter
import sqlite3
import os
from datetime import datetime, timedelta

DATABASE_PATH = 'databases/Run Sheet Database.db'

def save_run_sheet_to_excel():
    def is_valid_number(value):
        return value not in (None, '', ' ')

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM 'Run Sheet'")
    runsheet = cursor.fetchall()
    connection.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Run Sheet"

    NUM_ROWS_PER_REGION = 19
    NUM_COLUMNS = 9
    COLUMN_WIDTHS = [15, 25, 20, 12, 10, 10, 10, 12, 10]

    region_layout = {
        "North Shore": (2, 1),
        "Quebec": (22, 1),
        "Montreal": (42, 1),
        "Ontario": (62, 1),
        "Drummond": (2, 12),
        "Beauce": (22, 12),
        "South Shore": (42, 12),
        "Sherbrooke": (62, 12)
    }

    regions = list(region_layout.keys())

    for col_idx, width in enumerate(COLUMN_WIDTHS, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = width
        ws.column_dimensions[get_column_letter(col_idx + 11)].width = width

    thin_border = Border(left=Side(style='thin'),
                         right=Side(style='thin'),
                         top=Side(style='thin'),
                         bottom=Side(style='thin'))

    region_data = {region: [] for region in regions}
    for entry in runsheet:
        region_data[entry['Region']].append(entry)

    for region, (start_row, start_col) in region_layout.items():
        col_offset = start_col - 1
        row_offset = start_row - 1

        ws.merge_cells(start_row=start_row, start_column=start_col, end_row=start_row, end_column=start_col + 8)
        title_cell = ws.cell(row=start_row, column=start_col)
        title_cell.value = f"{region} - DRIVER:"
        title_cell.font = Font(bold=True)
        title_cell.alignment = Alignment(horizontal='center')

        headers = ["Customer ID", "Customer Name", "City", "Region", "Weight (lbs)", "Skids", "Bundles", "Coils", "Closing Time"]
        for idx, header in enumerate(headers):
            cell = ws.cell(row=start_row + 1, column=start_col + idx)
            cell.value = header
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')

        customers = region_data.get(region, [])[:16]
        for i, entry in enumerate(customers):
            ws.cell(row=start_row + 2 + i, column=start_col + 0).value = entry['Customer ID']
            ws.cell(row=start_row + 2 + i, column=start_col + 1).value = entry['Customer Name']
            ws.cell(row=start_row + 2 + i, column=start_col + 2).value = entry['City']
            ws.cell(row=start_row + 2 + i, column=start_col + 3).value = entry['Region']

            if is_valid_number(entry['Weight']):
                ws.cell(row=start_row + 2 + i, column=start_col + 4).value = float(entry['Weight'])
            if is_valid_number(entry['Skids']):
                ws.cell(row=start_row + 2 + i, column=start_col + 5).value = int(float(entry['Skids']))
            if is_valid_number(entry['Bundles']):
                ws.cell(row=start_row + 2 + i, column=start_col + 6).value = int(float(entry['Bundles']))
            if is_valid_number(entry['Coils']):
                ws.cell(row=start_row + 2 + i, column=start_col + 7).value = int(float(entry['Coils']))

            ws.cell(row=start_row + 2 + i, column=start_col + 8).value = entry['Closing Time']

        total_weight = sum(float(e['Weight']) for e in customers if is_valid_number(e['Weight']))
        total_skids = sum(int(float(e['Skids'])) for e in customers if is_valid_number(e['Skids']))
        total_bundles = sum(int(float(e['Bundles'])) for e in customers if is_valid_number(e['Bundles']))
        total_coils = sum(int(float(e['Coils'])) for e in customers if is_valid_number(e['Coils']))

        ws.cell(row=start_row + 18, column=start_col + 3).value = "Totals:"
        ws.cell(row=start_row + 18, column=start_col + 4).value = total_weight
        ws.cell(row=start_row + 18, column=start_col + 5).value = total_skids
        ws.cell(row=start_row + 18, column=start_col + 6).value = total_bundles
        ws.cell(row=start_row + 18, column=start_col + 7).value = total_coils

        for r in range(start_row, start_row + NUM_ROWS_PER_REGION):
            for c in range(start_col, start_col + NUM_COLUMNS):
                ws.cell(row=r, column=c).border = thin_border

    today = datetime.now()
    if today.weekday() == 4:
        target_date = today + timedelta(days=3)
    elif today.weekday() >= 5:
        target_date = today + timedelta(days=(7 - today.weekday()))
    else:
        target_date = today + timedelta(days=1)

    day_name = target_date.strftime('%A').upper()
    file_date = target_date.strftime('%m.%d.%Y')
    filename = f"{day_name} RUN SHEET {file_date}.xlsx"
    month_year_folder = target_date.strftime('%B %Y').upper()

    backup_base_dir = os.path.join(os.getcwd(), 'backups')
    backup_folder = os.path.join(backup_base_dir, month_year_folder)

    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)

    backup_path = os.path.join(backup_folder, filename)
    wb.save(backup_path)

    return backup_path

def get_latest_runsheet_filename():
    today = datetime.now()
    if today.weekday() == 4:
        target_date = today + timedelta(days=3)
    elif today.weekday() >= 5:
        target_date = today + timedelta(days=(7 - today.weekday()))
    else:
        target_date = today + timedelta(days=1)

    day_name = target_date.strftime('%A').upper()
    file_date = target_date.strftime('%m.%d.%Y')
    filename = f"{day_name} RUN SHEET {file_date}.xlsx"
    month_year_folder = target_date.strftime('%B %Y').upper()
    return filename, month_year_folder

