from flask import Blueprint, render_template, request, redirect, url_for, flash
import sqlite3

pickup_bp = Blueprint('pickup', __name__)

DATABASE_PATH = 'databases/Run Sheet Database.db'

def get_all_pickups():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    query = '''
        SELECT 
            rowid AS id,
            "Vendor Name" AS vendor_name,
            "Customer ID" AS customer_id,
            "Address" AS address,
            "City" AS city,
            "Region" AS region,
            "Province" AS province,
            "Postal Code" AS postal_code
        FROM Pickup
    '''
    pickups = conn.execute(query).fetchall()
    conn.close()
    return pickups

@pickup_bp.route('/add_pickups')
def add_pickups():
    pickups = get_all_pickups()
    return render_template('add_pickups.html', pickups=pickups)

def get_vendor_by_id(vendor_id):
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    vendor = conn.execute(
        '''
        SELECT rowid AS id,
                "Customer ID" AS customer_id,
               "Vendor Name" AS vendor_name,
               "Address" AS address,
               "City" AS city,
               "Region" AS region,
               "Province" AS province,
               "Postal Code" AS postal_code
        FROM Pickup
        WHERE rowid = ?
        ''', (vendor_id,)
    ).fetchone()
    conn.close()
    return vendor


@pickup_bp.route('/add_pickup_to_runsheet/<int:pickup_id>', methods=['GET'])
def show_pickup_form(pickup_id):
    pickup = get_vendor_by_id(pickup_id)
    if not pickup:
        flash('Vendor not found.')
        return redirect(url_for('pickup.add_pickups'))
    return render_template('add_pickups_to_runsheet.html', pickup=pickup)

@pickup_bp.route('/add_pickup_to_runsheet/<int:pickup_id>', methods=['POST'])
def submit_pickup_to_runsheet(pickup_id):
    data = request.form
    vendor = get_vendor_by_id(pickup_id)

    if not vendor:
        flash('Vendor not found.')
        return redirect(url_for('pickup.add_pickups'))

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO "Run Sheet" 
        ("Customer ID", "Customer Name", "Address", "City", "Region", "Province", "Postal Code", 
         "Weight", "Skids", "Bundles", "Coils", "Pickup", "Closing Time")
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        vendor['customer_id'] if vendor['customer_id'] else "",  # <-- this line changed
        vendor['vendor_name'],
        vendor['address'],
        vendor['city'],
        vendor['region'],
        vendor['province'],
        vendor['postal_code'],
        int(data.get('weight', 0) or 0),
        int(data.get('skids', 0) or 0),
        int(data.get('bundles', 0) or 0),
        int(data.get('coils', 0) or 0),
        'Y',
        data.get('closing_time', '16:00')
    ))
    conn.commit()
    conn.close()

    flash(f'Successfully added {vendor["vendor_name"]} to {vendor["region"]} region.')
    return redirect(url_for('home.home'))

@pickup_bp.route('/edit_vendor/<int:vendor_id>', methods=['GET', 'POST'])
def edit_vendor(vendor_id):
    conn = conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if request.method == 'POST':
        comment = request.form['comment']
        vendor_name = request.form['vendor_name']
        address = request.form['address']
        city = request.form['city']
        region = request.form['region']
        province = request.form['province']
        postal_code = request.form['postal_code']

        c.execute("""
            UPDATE Pickup
            SET "Vendor Name" = ?,"Customer ID" = ?, "Address" = ?, "City" = ?, "Region" = ?, "Province" = ?, "Postal Code" = ?
            WHERE rowid = ?
        """, (vendor_name, comment, address, city, region, province, postal_code, vendor_id))
        conn.commit()
        conn.close()
        flash('Vendor updated successfully.')
        return redirect(url_for('pickup.add_pickups'))

    # GET request with aliasing
    c.execute("""
        SELECT rowid AS id,
                "Customer ID" AS customer_id,
               "Vendor Name" AS vendor_name,
               "Address" AS address,
               "City" AS city,
               "Region" AS region,
               "Province" AS province,
               "Postal Code" AS postal_code
        FROM Pickup
        WHERE rowid = ?
    """, (vendor_id,))
    vendor = c.fetchone()
    conn.close()

    if not vendor:
        flash("Vendor not found.")
        return redirect(url_for('pickup.add_pickups'))

    return render_template('edit_vendor.html', vendor=vendor)


@pickup_bp.route('/add_vendor_form', methods=['GET', 'POST'])
def add_vendor_form():
    if request.method == 'POST':
        comment = request.form['comment']
        vendor_name = request.form['vendor_name']
        address = request.form['address']
        city = request.form['city']
        region = request.form['region']
        province = request.form['province']
        postal_code = request.form['postal_code']

        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT INTO Pickup ("Vendor Name","Customer ID", "Address", "City", "Region", "Province", "Postal Code")
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (comment, vendor_name, address, city, region, province, postal_code))
        conn.commit()
        conn.close()

        flash('Vendor added successfully.')
        return redirect(url_for('pickup.add_pickups'))

    return render_template('add_vendor.html')

@pickup_bp.route('/delete_vendor/<int:vendor_id>')
def delete_vendor(vendor_id):
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM Pickup WHERE rowid = ?', (vendor_id,))
    conn.commit()
    conn.close()
    flash("Vendor deleted successfully.")
    return redirect(url_for('pickup.add_pickups'))
