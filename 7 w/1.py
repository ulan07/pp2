import psycopg2

try:
    conn = psycopg2.connect(
        dbname="phonebook_db",
        user="postgres",        # твой username
        password="12345678",
        host="localhost",
        port="5432"
        options='-c client_encoding=UTF8'
    )
    cur = conn.cursor()
    print("Connection successful!")
except Exception as e:
    print("Error connecting to database:", e)

create_table_query = """
CREATE TABLE IF NOT EXISTS contacts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    email VARCHAR(50)
);
"""
cur.execute(create_table_query)
conn.commit()
print("Table created successfully!")