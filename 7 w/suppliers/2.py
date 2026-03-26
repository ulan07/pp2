import psycopg2
from config import load_config
import csv


def create_table():
    sql = """
    CREATE TABLE IF NOT EXISTS phonebook (
        contact_id SERIAL PRIMARY KEY,
        first_name VARCHAR(100) NOT NULL,
        phone VARCHAR(20) NOT NULL UNIQUE
    );
    """
    config = load_config()
    with psycopg2.connect(**config) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()


def add_contact(first_name, phone):
    sql = "INSERT INTO phonebook(first_name, phone) VALUES(%s, %s) RETURNING contact_id;"
    config = load_config()
    try:
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (first_name, phone))
                contact_id = cur.fetchone()[0]
                conn.commit()
                print(f"Contact added with id {contact_id}")
    except Exception as e:
        print("Error:", e)


def add_contacts_from_csv(csv_file):
    config = load_config()
    try:
        with open(csv_file, newline='') as f:
            reader = csv.reader(f)
            contacts = [(row[0], row[1]) for row in reader]
        sql = "INSERT INTO phonebook(first_name, phone) VALUES(%s, %s)"
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                cur.executemany(sql, contacts)
                conn.commit()
                print(f"{len(contacts)} contacts added from CSV")
    except Exception as e:
        print("Error:", e)


def update_contact(contact_id, new_name=None, new_phone=None):
    config = load_config()
    try:
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                if new_name:
                    cur.execute("UPDATE phonebook SET first_name=%s WHERE contact_id=%s", (new_name, contact_id))
                if new_phone:
                    cur.execute("UPDATE phonebook SET phone=%s WHERE contact_id=%s", (new_phone, contact_id))
                conn.commit()
                print(f"Contact {contact_id} updated")
    except Exception as e:
        print("Error:", e)

def delete_contact(contact_id=None, phone=None):
    config = load_config()
    try:
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                if contact_id:
                    cur.execute("DELETE FROM phonebook WHERE contact_id=%s", (contact_id,))
                elif phone:
                    cur.execute("DELETE FROM phonebook WHERE phone=%s", (phone,))
                conn.commit()
                print("Contact deleted")
    except Exception as e:
        print("Error:", e)


def query_contacts(name=None, phone_prefix=None):
    config = load_config()
    try:
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                sql = "SELECT contact_id, first_name, phone FROM phonebook WHERE 1=1"
                params = []
                if name:
                    sql += " AND first_name ILIKE %s"
                    params.append(f"%{name}%")
                if phone_prefix:
                    sql += " AND phone LIKE %s"
                    params.append(f"{phone_prefix}%")
                cur.execute(sql, params)
                rows = cur.fetchall()
                for row in rows:
                    print(row)
    except Exception as e:
        print("Error:", e)
    
if __name__ == '__main__':
    create_table()

    
    add_contact("Alice", "1234567890")
    
    
    add_contacts_from_csv("contacts.csv")
    
   
    update_contact(1, new_name="Alicia", new_phone="0987654321")
    
   
    query_contacts(name="Ali")
    
    
    query_contacts(phone_prefix="123")
    
   
    delete_contact(contact_id=1)
    
  
    delete_contact(phone="1234567890")