from connect import get_connection

def call_function(cur, query, params):
    cur.execute(query, params)
    return cur.fetchall()

def call_procedure(cur, query, params):
    cur.execute(query, params)

def main():
    conn = get_connection()
    cur = conn.cursor()

    while True:
        print("\n1.Search")
        print("2.Pagination")
        print("3.Upsert")
        print("4.Bulk insert")
        print("5.Delete")
        print("6.Exit")

        choice = input("Choose: ")

        if choice == "1":
            pattern = input("Enter search: ")
            result = call_function(
                cur,
                "SELECT * FROM search_contacts(%s)",
                (pattern,)
            )
            print(result)

        elif choice == "2":
            limit = int(input("Limit: "))
            offset = int(input("Offset: "))
            result = call_function(
                cur,
                "SELECT * FROM get_contacts_paginated(%s, %s)",
                (limit, offset)
            )
            print(result)

        elif choice == "3":
            name = input("Name: ")
            phone = input("Phone: ")
            call_procedure(
                cur,
                "CALL upsert_contact(%s, %s)",
                (name, phone)
            )
            conn.commit()
            print("Done")

        elif choice == "4":
            names = input("Names (comma): ").split(",")
            phones = input("Phones (comma): ").split(",")

            call_procedure(
                cur,
                "CALL bulk_insert_contacts(%s, %s)",
                (names, phones)
            )
            conn.commit()
            print("Done")

        elif choice == "5":
            value = input("Name or phone: ")
            call_procedure(
                cur,
                "CALL delete_contact(%s)",
                (value,)
            )
            conn.commit()
            print("Deleted")

        elif choice == "6":
            break

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()