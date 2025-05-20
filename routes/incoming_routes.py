from flask import Blueprint, render_template, request, redirect, url_for, flash
import sqlite3
import os

incoming_bp = Blueprint('incoming', __name__)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'databases', 'Run Sheet DataBase.db')

@incoming_bp.route('/incoming_material')
def view_incoming_material():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    incoming = conn.execute('SELECT * FROM IncomingMaterial ORDER BY date DESC').fetchall()
    conn.close()
    return render_template('incoming_material.html', incoming=incoming)

@incoming_bp.route('/delete_incoming_material/<int:id>')
def delete_incoming_material(id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute('DELETE FROM IncomingMaterial WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Entry deleted successfully.')
    return redirect(url_for('incoming.view_incoming_material'))

@incoming_bp.route('/mark_incoming_received/<int:id>')
def mark_incoming_received(id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute('UPDATE IncomingMaterial SET received = 1 WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Marked as received.')
    return redirect(url_for('incoming.view_incoming_material'))

from flask import jsonify

@incoming_bp.route('/api/incoming_material')
def api_incoming_material():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT rowid, * FROM IncomingMaterial ORDER BY date DESC")
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@incoming_bp.route('/add_incoming', methods=['GET', 'POST'])
def add_incoming():
    if request.method == 'POST':
        form = request.form
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT INTO IncomingMaterial (
                date, initials, supplier, location, contact, "PO#",
                notes, material, "weight/lbs", "PU Date", carrier,
                "border crossing", rate, "invoice approved", "rate confirmed",
                "bl sent", customs, received
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'N')
        """, (
            form['date'], form['initials'], form['supplier'], form['location'],
            form['contact'], form['ponum'], form['notes'], form['material'],
            form['weight_lbs'], form['pu_date'], form['carrier'],
            form['border_crossing'], form['rate'], form['invoice_approved'],
            form['rate_confirmed'], form['bl_sent'], form['customs']
        ))
        conn.commit()
        conn.close()
        flash('Incoming entry added.')
        return redirect(url_for('incoming.view_incoming_material'))

    return render_template('add_incoming.html')

@incoming_bp.route('/api/suggestions/<column>')
def get_suggestions(column):
    allowed_columns = {
        'supplier': '"Supplier"',
        'location': '"Location"',
        'contact': '"Contact"',
        'carrier': '"Carrier"',
        'material': '"Material"',
        'customs': '"Customs"',
        'rate': '"Rate"',
        'initials': '"Initials"',
        'border_crossing': '"border crossing"'
    }

    if column not in allowed_columns:
        return jsonify([])

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute(f"""
            SELECT DISTINCT {allowed_columns[column]}
            FROM incomingmaterial
            WHERE {allowed_columns[column]} IS NOT NULL
        """)
        results = [row[0] for row in c.fetchall()]
    except sqlite3.OperationalError as e:
        print(f"Suggestion query error: {e}")
        results = []
    finally:
        conn.close()

    return jsonify(results)

@incoming_bp.route('/delete_incoming/<int:row_id>', methods=['POST'])
def delete_incoming(row_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("DELETE FROM incomingmaterial WHERE rowid = ?", (row_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error deleting row: {e}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@incoming_bp.route("/api/incoming")
def get_incoming_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT date, "PU Date", supplier, "PO#", material
        FROM IncomingMaterial
        WHERE TRIM(UPPER(received)) != 'Y'
    """)
    rows = cur.fetchall()
    return jsonify([dict(row) for row in rows])
@incoming_bp.route("/incoming")
def view_incoming_unreceived():
    return render_template("incoming.html")

@incoming_bp.route("/api/incoming_containers")
def get_incoming_containers():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM incoming_containers ORDER BY eta ASC")
    return jsonify([dict(row) for row in cur.fetchall()])


@incoming_bp.route("/incoming_containers")
def view_incoming_containers():
    return render_template("incoming_containers.html")
