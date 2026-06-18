import psycopg2
from config import load_config

def get_vendors():
    config = load_config()
    try:
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT vendor_id, vendor_name FROM vendors ORDER BY vendor_name")
                print("Количество поставщиков: ", cur.rowcount)
                row = cur.fetchone()
                while row is not None:
                    print(row)
                    row = cur.fetchone()
    except Exception as error:
        print(error)

if __name__ == '__main__':
    get_vendors()