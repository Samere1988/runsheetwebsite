from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory,jsonify
import sqlite3
import os
import openpyxl
from openpyxl.utils.cell import coordinate_from_string, column_index_from_string
from .save_runsheet import save_run_sheet_to_excel, get_latest_runsheet_filename
from datetime import time


runsheet_bp = Blueprint('runsheet', __name__)

DATABASE_PATH = 'databases/Run Sheet Database.db'

# -------------------
# View Run Sheet
# -------------------
@runsheet_bp.route('/view_run_sheet')
def view_run_sheet():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM 'Run Sheet'")
    runsheet = cursor.fetchall()
    connection.close()

    regions = ['North Shore', 'Quebec', 'Montreal', 'Ontario', 'Drummond', 'Beauce', 'South Shore', 'Sherbrooke']
    region_data = {region: [] for region in regions}
    region_totals = {region: {"Weight": 0, "Skids": 0, "Bundles": 0, "Coils": 0} for region in regions}

    def safe_int(value):
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return 0

    for entry in runsheet:
        region = entry['Region']
        if region in region_data and entry['Customer ID']:
            region_data[region].append(entry)
            region_totals[region]["Weight"] += safe_int(entry['Weight'])
            region_totals[region]["Skids"] += safe_int(entry['Skids'])
            region_totals[region]["Bundles"] += safe_int(entry['Bundles'])
            region_totals[region]["Coils"] += safe_int(entry['Coils'])

    # ⬇️ Define dummy driver info so the template can access it
    driver_info = {
        region: {
            "name": "____________________",
            "start_time": "________________"
        } for region in regions
    }

    return render_template(
        'view_run_sheet.html',
        region_data=region_data,
        region_totals=region_totals,
        driver_info=driver_info  # ✅ ADD THIS LINE
    )

# -------------------
# Add Customer
# -------------------
@runsheet_bp.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        customer_id = request.form['customer_id']
        customer_name = request.form['customer_name']
        address = request.form['address']
        city = request.form['city']
        province = request.form['province']
        postal_code = request.form['postal_code']
        region = request.form['region']
        weight = float(request.form['weight'] or 0)
        skids = int(request.form['skids'] or 0)
        bundles = int(request.form['bundles'] or 0)
        coils = int(request.form['coils'] or 0)
        closing_time = request.form['closing_time']
        pickup = request.form['pickup']

        connection = sqlite3.connect(DATABASE_PATH)
        connection.row_factory = sqlite3.Row  # ADD THIS LINE
        cursor = connection.cursor()

        # Check if this customer+region already exists
        cursor.execute('''
            SELECT * FROM "Run Sheet" WHERE "Customer ID" = ? AND "Region" = ?
        ''', (customer_id, region))
        existing = cursor.fetchone()

        if existing:
            # Sum the numeric values and update
            new_weight = float(existing['Weight'] or 0) + weight
            new_skids = int(existing['Skids'] or 0) + skids
            new_bundles = int(existing['Bundles'] or 0) + bundles
            new_coils = int(existing['Coils'] or 0) + coils

            cursor.execute('''
                UPDATE "Run Sheet"
                SET "Weight" = ?, "Skids" = ?, "Bundles" = ?, "Coils" = ?, "Closing Time" = ?, "Pickup" = ?
                WHERE "Customer ID" = ? AND "Region" = ?
            ''', (new_weight, new_skids, new_bundles, new_coils, closing_time, pickup, customer_id, region))
        else:
            # Insert as new entry
            cursor.execute('''
                INSERT INTO "Run Sheet" 
                ("Customer ID", "Customer Name", "Address", "City", "Province", "Postal Code", "Region", 
                "Weight", "Skids", "Bundles", "Coils", "Closing Time", "Pickup")
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (customer_id, customer_name, address, city, province, postal_code, region,
                  weight, skids, bundles, coils, closing_time, pickup))

        connection.commit()
        connection.close()

        flash(f"✅ Successfully added {customer_name} to {region} region.")
        return redirect(url_for('runsheet.add_customer'))

    return render_template('add_customer.html')



# -------------------
# Import Run Sheet
# -------------------

@runsheet_bp.route('/import_run_sheet', methods=['GET'])
def show_import_form():
    return render_template('import_run_sheet.html')

@runsheet_bp.route('/import_run_sheet', methods=['POST'])
def import_run_sheet():
    file = request.files.get('file')
    if not file:
        flash('No file selected.')
        return redirect(url_for('runsheet.view_run_sheet'))

    wb = openpyxl.load_workbook(file, data_only=True)
    ws = wb.active

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    cursor.execute("DELETE FROM 'Run Sheet'")

    region_blocks = {
        'North Shore': ('A3', 'I18'),
        'Quebec': ('A22', 'I37'),
        'Montreal': ('A41', 'I56'),
        'Ontario': ('A60', 'I75'),
        'Drummond': ('K3', 'S18'),
        'Beauce': ('K22', 'S37'),
        'South Shore': ('K41', 'S56'),
        'Sherbrooke': ('K60', 'S75')
    }

    def safe_string(value):
        if value is None:
            return ''
        if isinstance(value, time):
            return value.strftime('%H:%M')
        return str(value).strip()

    for region, (start_cell, end_cell) in region_blocks.items():
        start_col_letter, start_row = coordinate_from_string(start_cell)
        end_col_letter, end_row = coordinate_from_string(end_cell)
        start_col = column_index_from_string(start_col_letter)
        end_col = column_index_from_string(end_col_letter)

        for row in ws.iter_rows(min_row=start_row, max_row=end_row, min_col=start_col, max_col=end_col, values_only=True):
            if not row or all(cell is None or str(cell).strip() == '' for cell in row):
                continue

            customer_id = safe_string(row[0])
            customer_name = safe_string(row[1])
            city = safe_string(row[2])
            weight = safe_string(row[3])
            skids = safe_string(row[4])
            bundles = safe_string(row[5])
            coils = safe_string(row[6])
            closing_time = safe_string(row[7])
            pickup = safe_string(row[8])

            cursor.execute('''
                INSERT INTO "Run Sheet" 
                ("Customer ID", "Customer Name", "City", "Weight", "Skids", "Bundles", "Coils", "Closing Time", "Pickup", "Region")
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (customer_id, customer_name, city, weight, skids, bundles, coils, closing_time, pickup, region))

    connection.commit()
    connection.close()
    flash('✅ Successfully imported new Run Sheet!')
    return redirect(url_for('runsheet.view_run_sheet'))

# -------------------
# Clear Run Sheet
# -------------------
@runsheet_bp.route('/clear_run_sheet')
def clear_run_sheet():
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()
    cursor.execute("DELETE FROM 'Run Sheet'")
    connection.commit()
    connection.close()
    flash('✅ Successfully cleared the Run Sheet.')
    return redirect(url_for('runsheet.view_run_sheet'))

# -------------------
# Save and Download Run Sheet
# -------------------
@runsheet_bp.route('/save_run_sheet')
def save_run_sheet():
    try:
        save_run_sheet_to_excel()
        return redirect(url_for('runsheet.download_run_sheet'))
    except Exception as e:
        print("Error saving run sheet:", str(e))
        return "Failed to save run sheet.", 500

@runsheet_bp.route('/download_run_sheet')
def download_run_sheet():
    backups_dir = os.path.join(os.getcwd(), 'backups')
    latest_filename, folder = get_latest_runsheet_filename()
    return send_from_directory(directory=os.path.join(backups_dir, folder), path=latest_filename, as_attachment=True)

# -------------------
# Delete Run Customer
# -------------------
@runsheet_bp.route('/delete_run_customer', methods=['POST'])
def delete_run_customer():
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    id = request.form.get('id')
    customer_id = request.form.get('customer_id')
    region = request.form.get('region')

    if id:
        cursor.execute("DELETE FROM 'Run Sheet' WHERE id = ?", (id,))
    elif customer_id and region:
        cursor.execute("DELETE FROM 'Run Sheet' WHERE `Customer ID` = ? AND `Region` = ?", (customer_id, region))
    else:
        connection.close()
        return "Cannot delete: no valid identifier found.", 400

    connection.commit()
    connection.close()
    return redirect(url_for('runsheet.view_run_sheet'))

# -------------------
# Placeholder for Edit
# -------------------
@runsheet_bp.route('/edit_customer/<customer_id>', methods=['GET', 'POST'])
def edit_run_customer(customer_id):
    return f"Edit page for customer ID {customer_id} coming soon."

@runsheet_bp.route('/lookup_customer/<customer_id>')
def lookup_customer(customer_id):
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM 'Customer List' WHERE `Customer ID` = ?", (customer_id,))

    row = cursor.fetchone()
    connection.close()

    if row:
        result = {key: row[key] for key in row.keys()}
        result['found'] = True
        return jsonify(result)
    else:
        return jsonify({'found': False}), 404

