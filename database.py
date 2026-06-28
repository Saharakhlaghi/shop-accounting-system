import sqlite3

conn = sqlite3.connect('accounting.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    customer_code TEXT UNIQUE NOT NULL,
    phone TEXT NOT NULL,
    address TEXT,
    description TEXT
)
''')


cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    product TEXT NOT NULL,
    purchase_amount REAL NOT NULL,
    selling_amount REAL NOT NULL,
    profit REAL,
    deposit REAL,
    remaining_balance REAL,
    registration_date TEXT NOT NULL,
    delivery_date TEXT,
    delivery_address TEXT,
    delivered INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
)
''')

conn.commit()
conn.close()