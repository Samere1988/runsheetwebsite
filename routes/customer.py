from flask import Blueprint, render_template, request, redirect, url_for
import sqlite3

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/view_customer_database')
def view_customer_database():
    connection = sqlite3.connect('databases/Run Sheet Database.db')
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM 'Customer List'")
    customers = cursor.fetchall()
    connection.close()
    return render_template('view_customer_database.html', customers=customers)

@customer_bp.route('/delete_customer/<customer_id>', methods=['POST'])
def delete_customer(customer_id):
    connection = sqlite3.connect('databases/Run Sheet Database.db')
    cursor = connection.cursor()
    cursor.execute("DELETE FROM 'Customer List' WHERE `Customer ID` = ?", (customer_id,))
    connection.commit()
    connection.close()
    return redirect(url_for('customer.view_customer_database'))
@customer_bp.route('/edit_customer/<customer_id>', methods=['GET'])
def edit_customer(customer_id):
    connection = sqlite3.connect('databases/Run Sheet Database.db')
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM 'Customer List' WHERE `Customer ID` = ?", (customer_id,))
    customer = cursor.fetchone()
    connection.close()
    return render_template('edit_customer.html', customer=customer)

@customer_bp.route('/update_customer/<customer_id>', methods=['POST'])
def update_customer(customer_id):
    customer_name = request.form['customer_name']
    address = request.form['address']
    city = request.form['city']
    province = request.form['province']
    postal_code = request.form['postal_code']
    region = request.form['region']

    connection = sqlite3.connect('databases/Run Sheet Database.db')
    cursor = connection.cursor()
    cursor.execute("""
        UPDATE 'Customer List'
        SET `Customer Name` = ?, `Address` = ?, `City` = ?, `Province` = ?, `Postal Code` = ?, `Region` = ?
        WHERE `Customer ID` = ?
    """, (customer_name, address, city, province, postal_code, region, customer_id))
    connection.commit()
    connection.close()
    return redirect(url_for('customer.view_customer_database'))
