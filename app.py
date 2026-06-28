import sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify
import datetime
import jdatetime  

app = Flask(__name__)


def get_customers():
    conn = sqlite3.connect('accounting.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers")
    customers = cursor.fetchall()
    conn.close()
    return customers

@app.route('/')
def home():
    query = request.args.get('q', '')
    conn = sqlite3.connect('accounting.db')
    conn.row_factory = sqlite3.Row  
    cursor = conn.cursor()
    if query:
        cursor.execute(
          "SELECT c.*, (SELECT COUNT(*) FROM orders WHERE orders.customer_id = c.id) as order_count FROM customers c WHERE c.name LIKE ?",
          ('%' + query + '%',)
        )
    else:
        cursor.execute(
          "SELECT c.*, (SELECT COUNT(*) FROM orders WHERE orders.customer_id = c.id) as order_count FROM customers c"
        )
    customers = cursor.fetchall()
    conn.close()
    return render_template('index.html', customers=customers, q=query)

@app.route('/add', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        name = request.form['name']
        customer_code = request.form['customer_code']
        phone = request.form['phone']
        address = request.form['address']
        description = request.form['description']
        try:
            conn = sqlite3.connect('accounting.db')
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO customers (name, customer_code, phone, address, description)
                VALUES (?, ?, ?, ?, ?)
            """, (name, customer_code, phone, address, description))
            conn.commit()
        except Exception as e:
            print("خطا در اضافه کردن مشتری:", e)
        finally:
            conn.close()
        return redirect(url_for('home'))
    else:
        return render_template('add_customer.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_customer(id):
    conn = sqlite3.connect('accounting.db')
    cursor = conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        customer_code = request.form['customer_code']
        phone = request.form['phone']
        address = request.form['address']
        description = request.form['description']
        cursor.execute("""
            UPDATE customers
            SET name = ?, customer_code = ?, phone = ?, address = ?, description = ?
            WHERE id = ?
        """, (name, customer_code, phone, address, description, id))
        conn.commit()
        conn.close()
        return redirect(url_for('home'))
    else:
        cursor.execute("SELECT * FROM customers WHERE id = ?", (id,))
        customer = cursor.fetchone()
        conn.close()
        return render_template('edit_customer.html', customer=customer)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_customer(id):
    conn = sqlite3.connect('accounting.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customers WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

@app.route('/customers/search')
def search_customers():
    q = request.args.get('q', '')
    conn = sqlite3.connect('accounting.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, phone FROM customers WHERE name LIKE ?", ('%' + q + '%',))
    results = cursor.fetchall()
    conn.close()
    customers = [dict(row) for row in results]
    return jsonify(customers)



@app.route('/orders/active')
def orders_active():
    q = request.args.get('q', '')
    conn = sqlite3.connect('accounting.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    sql = """
       SELECT orders.*, customers.name AS customer_name
       FROM orders LEFT JOIN customers ON orders.customer_id = customers.id
       WHERE orders.delivered = 0
    """
    params = []
    if q:
        sql += " AND customers.name LIKE ?"
        params.append("%" + q + "%")
    cursor.execute(sql, params)
    active_orders = cursor.fetchall()
    conn.close()

 
    orders = []
    for order in active_orders:
        order_dict = dict(order)  
        orders.append(order_dict)

    return render_template('orders_active.html', orders=orders, q=q)

@app.route('/orders/inactive')
def orders_inactive():
    q = request.args.get('q', '')
    conn = sqlite3.connect('accounting.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    sql = """
       SELECT orders.*, customers.name AS customer_name
       FROM orders LEFT JOIN customers ON orders.customer_id = customers.id
       WHERE orders.delivered = 1
    """
    params = []
    if q:
        sql += " AND customers.name LIKE ?"
        params.append("%" + q + "%")
    cursor.execute(sql, params)
    inactive_orders = cursor.fetchall()
    conn.close()
    orderss = []
    for order in inactive_orders:
        order_dict = dict(order)  
        orderss.append(order_dict)
    return render_template('orders_inactive.html', orders=orderss, q=q)



@app.route('/orders/add', methods=['GET', 'POST'])
def add_order():
    if request.method == 'POST':
        customer_id = request.form['customer_id']
        product = request.form['product']
        purchase_amount = float(request.form['purchase_amount'])
        selling_amount = float(request.form['selling_amount'])
        profit = selling_amount - purchase_amount
        deposit = float(request.form['deposit']) if request.form['deposit'] else 0.0
        remaining_balance = selling_amount - deposit
        
        registration_date = request.form['registration_date']
        delivery_date = request.form['delivery_date']
        
      
        
        if 'send_to_customer_address' in request.form:
            
            conn_temp = sqlite3.connect('accounting.db')
            
            temp_cursor = conn_temp.cursor()
            temp_cursor.execute("SELECT address FROM customers WHERE id = ?", (customer_id,))
            row = temp_cursor.fetchone()
            conn_temp.close()
            delivery_address = row[0] if row else ''
        else:
            delivery_address = request.form.get('delivery_address', '')
        
        delivered = 1 if ('delivered' in request.form and request.form['delivered'] == 'on') else 0

        conn = sqlite3.connect('accounting.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO orders 
            (customer_id, product, purchase_amount, selling_amount, profit, deposit, remaining_balance, registration_date, delivery_date, delivery_address, delivered)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            customer_id, product, purchase_amount, selling_amount, profit, deposit,
            remaining_balance, registration_date, delivery_date, delivery_address, delivered
        ))
        conn.commit()
        conn.close()
        return redirect(url_for('orders_active'))
    else:
        return render_template('add_order.html')

@app.route('/orders/edit/<int:order_id>', methods=['GET', 'POST'])
def edit_order(order_id):
    conn = sqlite3.connect('accounting.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if request.method == 'POST':
        customer_id = request.form['customer_id']
        product = request.form['product']
        purchase_amount = float(request.form['purchase_amount'])
        selling_amount = float(request.form['selling_amount'])
        profit = selling_amount - purchase_amount
        deposit = float(request.form['deposit']) if request.form['deposit'] else 0.0
        remaining_balance = selling_amount - deposit
        registration_date = request.form['registration_date']
        delivery_date = request.form['delivery_date']
        
        if 'send_to_customer_address' in request.form:
            conn_temp = sqlite3.connect('accounting.db')
            temp_cursor = conn_temp.cursor()
            temp_cursor.execute("SELECT address FROM customers WHERE id = ?", (customer_id,))
            row = temp_cursor.fetchone()
            conn_temp.close()
            delivery_address = row[0] if row else ''
        else:
            delivery_address = request.form.get('delivery_address', '')
        
        delivered = 1 if ('delivered' in request.form and request.form['delivered'] == 'on') else 0

        cursor.execute("""
            UPDATE orders 
            SET customer_id = ?, product = ?, purchase_amount = ?, selling_amount = ?, profit = ?, deposit = ?, remaining_balance = ?, registration_date = ?, delivery_date = ?, delivery_address = ?, delivered = ?
            WHERE id = ?
        """, (
            customer_id, product, purchase_amount, selling_amount, profit, deposit,
            remaining_balance, registration_date, delivery_date, delivery_address, delivered, order_id
        ))
        conn.commit()
        conn.close()
        return redirect(url_for('orders_active'))
    else:
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        order = cursor.fetchone()

  
        customer_id = order['customer_id']
        cursor.execute("SELECT name FROM customers WHERE id = ?", (customer_id,))
        customer = cursor.fetchone()
        customer_name = customer['name'] if customer else 'نامشخص'

        conn.close()

        return render_template('edit_order.html', order=order, customer_name=customer_name)


@app.route('/orders/delete/<int:order_id>', methods=['POST'])
def delete_order(order_id):
    conn = sqlite3.connect('accounting.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('orders_active'))

@app.route('/customer/<int:id>')
def customer_profile(id):
    conn = sqlite3.connect('accounting.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE id = ?", (id,))
    customer = cursor.fetchone()
    conn.close()
    return render_template('customer_profile.html', customer=customer)

@app.route('/customer/<int:id>/history')
def customer_history(id):
    conn = sqlite3.connect('accounting.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM orders WHERE customer_id = ?", (id,))
    orders = cursor.fetchall()

    cursor.execute("SELECT * FROM customers WHERE id = ?", (id,))
    customer = cursor.fetchone()
    conn.close()
    return render_template('customer_history.html', customer=customer, orders=orders)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)