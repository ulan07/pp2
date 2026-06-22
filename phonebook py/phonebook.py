import json
import csv
import os
from connect import get_connection

# ──────────────────────────────────────────────
#  DB helpers
# ──────────────────────────────────────────────
def call_function(cur, query, params=()):
    cur.execute(query, params)
    return cur.fetchall()

def call_procedure(cur, query, params=()):
    cur.execute(query, params)

def print_contacts(rows, headers=None):
    if not rows:
        print("  (нет результатов)")
        return
    if headers is None:
        headers = ["id", "Имя", "Email", "День рождения", "Группа", "Телефоны"]
    col_w = [max(len(str(headers[i])), max(len(str(r[i] or "")) for r in rows))
             for i in range(len(headers))]
    fmt = "  " + "  ".join(f"{{:<{w}}}" for w in col_w)
    print(fmt.format(*headers))
    print("  " + "-" * (sum(col_w) + 2 * len(col_w)))
    for r in rows:
        print(fmt.format(*[str(v or "") for v in r]))

# ──────────────────────────────────────────────
#  MENU SECTIONS
# ──────────────────────────────────────────────

# ── 1. Search ─────────────────────────────────
def menu_search(cur):
    print("\n--- Поиск ---")
    print("1. По имени / телефону / email")
    print("2. По группе")
    print("3. По email")
    ch = input("Выберите: ").strip()

    if ch == "1":
        q = input("Введите запрос: ")
        rows = call_function(cur, "SELECT * FROM search_contacts(%s)", (q,))
        print_contacts(rows)

    elif ch == "2":
        print("Группы: Family, Work, Friend, Other")
        g = input("Группа: ")
        rows = call_function(cur, "SELECT * FROM filter_by_group(%s)", (g,))
        print_contacts(rows, ["id","Имя","Email","День рождения","Телефоны"])

    elif ch == "3":
        q = input("Часть email (например gmail): ")
        rows = call_function(cur, "SELECT * FROM search_contacts(%s)", (q,))
        print_contacts(rows)

# ── 2. Pagination ─────────────────────────────
def menu_pagination(cur):
    print("\n--- Пагинация ---")
    limit  = int(input("Строк на странице: ") or "5")
    sort   = input("Сортировка (name/birthday/created_at) [name]: ").strip() or "name"
    grp_in = input("Фильтр по group_id (Enter = все): ").strip()
    group_id = int(grp_in) if grp_in.isdigit() else None

    offset = 0
    while True:
        rows = call_function(
            cur,
            "SELECT * FROM get_contacts_paginated(%s, %s, %s, %s)",
            (limit, offset, sort, group_id)
        )
        print(f"\n  Страница {offset//limit + 1}  (записи {offset+1}–{offset+len(rows)})")
        print_contacts(rows)
        print("  [n]ext  [p]rev  [q]uit")
        cmd = input("  > ").strip().lower()
        if cmd == "n":
            if len(rows) < limit:
                print("  Это последняя страница.")
            else:
                offset += limit
        elif cmd == "p":
            offset = max(0, offset - limit)
        elif cmd == "q":
            break

# ── 3. Upsert contact ─────────────────────────
def menu_upsert(cur, conn):
    print("\n--- Добавить / обновить контакт ---")
    name  = input("Имя: ").strip()
    email = input("Email (Enter = пропустить): ").strip() or None
    bday  = input("День рождения YYYY-MM-DD (Enter = пропустить): ").strip() or None
    print("Группы: Family, Work, Friend, Other")
    grp   = input("Группа (Enter = пропустить): ").strip() or None
    call_procedure(cur, "CALL upsert_contact(%s, %s, %s, %s)",
                   (name, email, bday, grp))
    conn.commit()
    print("  Сохранено.")

    add_ph = input("Добавить номер телефона? (y/n): ").strip().lower()
    if add_ph == "y":
        phone = input("Номер: ").strip()
        ptype = input("Тип (home/work/mobile) [mobile]: ").strip() or "mobile"
        call_procedure(cur, "CALL add_phone(%s, %s, %s)", (name, phone, ptype))
        conn.commit()
        print("  Телефон добавлен.")

# ── 4. Add phone ──────────────────────────────
def menu_add_phone(cur, conn):
    print("\n--- Добавить телефон ---")
    name  = input("Имя контакта: ").strip()
    phone = input("Номер: ").strip()
    ptype = input("Тип (home/work/mobile) [mobile]: ").strip() or "mobile"
    try:
        call_procedure(cur, "CALL add_phone(%s, %s, %s)", (name, phone, ptype))
        conn.commit()
        print("  Добавлено.")
    except Exception as e:
        conn.rollback()
        print(f"  Ошибка: {e}")

# ── 5. Move to group ──────────────────────────
def menu_move_group(cur, conn):
    print("\n--- Переместить в группу ---")
    name = input("Имя контакта: ").strip()
    grp  = input("Новая группа: ").strip()
    try:
        call_procedure(cur, "CALL move_to_group(%s, %s)", (name, grp))
        conn.commit()
        print("  Перемещено.")
    except Exception as e:
        conn.rollback()
        print(f"  Ошибка: {e}")

# ── 6. Bulk insert ────────────────────────────
def menu_bulk(cur, conn):
    print("\n--- Массовая вставка ---")
    names  = [n.strip() for n in input("Имена (через запятую): ").split(",")]
    phones = [p.strip() for p in input("Телефоны (через запятую): ").split(",")]
    types  = [t.strip() for t in input("Типы (через запятую, или Enter): ").split(",")]
    types  = types if any(types) else None
    try:
        call_procedure(cur, "CALL bulk_insert_contacts(%s, %s, %s)",
                       (names, phones, types))
        conn.commit()
        print("  Вставлено.")
    except Exception as e:
        conn.rollback()
        print(f"  Ошибка: {e}")

# ── 7. Delete ─────────────────────────────────
def menu_delete(cur, conn):
    print("\n--- Удалить контакт ---")
    val = input("Имя или телефон: ").strip()
    call_procedure(cur, "CALL delete_contact(%s)", (val,))
    conn.commit()
    print("  Удалено.")

# ── 8. Export to JSON ─────────────────────────
def menu_export_json(cur):
    print("\n--- Экспорт в JSON ---")
    cur.execute("""
        SELECT c.id, c.name, c.email, c.birthday::TEXT,
               g.name AS grp,
               JSON_AGG(
                   JSON_BUILD_OBJECT('phone', p.phone, 'type', p.type)
               ) FILTER (WHERE p.id IS NOT NULL) AS phones
        FROM contacts c
        LEFT JOIN groups g ON g.id = c.group_id
        LEFT JOIN phones p ON p.contact_id = c.id
        GROUP BY c.id, c.name, c.email, c.birthday, g.name
        ORDER BY c.name
    """)
    rows = cur.fetchall()
    data = []
    for r in rows:
        phones_raw = r[5]
        if isinstance(phones_raw, str):
            import json as _j
            phones_raw = _j.loads(phones_raw)
        data.append({
            "id":       r[0],
            "name":     r[1],
            "email":    r[2],
            "birthday": r[3],
            "group":    r[4],
            "phones":   phones_raw or [],
        })
    fname = input("Имя файла [contacts.json]: ").strip() or "contacts.json"
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Экспортировано {len(data)} контактов в {fname}")

# ── 9. Import from JSON ───────────────────────
def menu_import_json(cur, conn):
    print("\n--- Импорт из JSON ---")
    fname = input("Имя файла [contacts.json]: ").strip() or "contacts.json"
    if not os.path.exists(fname):
        print("  Файл не найден.")
        return

    with open(fname, "r", encoding="utf-8") as f:
        data = json.load(f)

    for contact in data:
        name  = contact.get("name", "").strip()
        if not name:
            continue

        # check duplicate
        cur.execute("SELECT id FROM contacts WHERE name = %s", (name,))
        existing = cur.fetchone()
        if existing:
            ans = input(f"  '{name}' уже существует. Перезаписать? (y/n): ").strip().lower()
            if ans != "y":
                continue
            cur.execute("DELETE FROM contacts WHERE name = %s", (name,))
            conn.commit()

        call_procedure(cur, "CALL upsert_contact(%s, %s, %s, %s)", (
            name,
            contact.get("email"),
            contact.get("birthday"),
            contact.get("group"),
        ))
        conn.commit()

        for ph in contact.get("phones") or []:
            try:
                call_procedure(cur, "CALL add_phone(%s, %s, %s)", (
                    name,
                    ph.get("phone", ""),
                    ph.get("type", "mobile"),
                ))
                conn.commit()
            except Exception:
                conn.rollback()

    print(f"  Импорт завершён ({len(data)} записей обработано).")

# ── 10. Import from CSV ───────────────────────
def menu_import_csv(cur, conn):
    print("\n--- Импорт из CSV ---")
    fname = input("Имя файла [contacts.csv]: ").strip() or "contacts.csv"
    if not os.path.exists(fname):
        print("  Файл не найден.")
        return

    imported = 0
    with open(fname, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name  = row.get("name", "").strip()
            phone = row.get("phone", "").strip()
            ptype = row.get("type", "mobile").strip() or "mobile"
            email = row.get("email", "").strip() or None
            bday  = row.get("birthday", "").strip() or None
            grp   = row.get("group", "").strip() or None

            if not name:
                continue

            try:
                call_procedure(cur, "CALL upsert_contact(%s, %s, %s, %s)",
                               (name, email, bday, grp))
                conn.commit()
                if phone:
                    call_procedure(cur, "CALL add_phone(%s, %s, %s)",
                                   (name, phone, ptype))
                    conn.commit()
                imported += 1
            except Exception as e:
                conn.rollback()
                print(f"  Пропущено '{name}': {e}")

    print(f"  Импортировано {imported} контактов.")

# ──────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────
def main():
    conn = get_connection()
    cur  = conn.cursor()

    while True:
        print("\n" + "="*40)
        print("  ТЕЛЕФОННАЯ КНИГА")
        print("="*40)
        print("1.  Поиск")
        print("2.  Пагинация / список")
        print("3.  Добавить / обновить контакт")
        print("4.  Добавить телефон")
        print("5.  Переместить в группу")
        print("6.  Массовая вставка")
        print("7.  Удалить контакт")
        print("8.  Экспорт в JSON")
        print("9.  Импорт из JSON")
        print("10. Импорт из CSV")
        print("0.  Выход")
        print("="*40)

        choice = input("Выберите: ").strip()

        try:
            if   choice == "1":  menu_search(cur)
            elif choice == "2":  menu_pagination(cur)
            elif choice == "3":  menu_upsert(cur, conn)
            elif choice == "4":  menu_add_phone(cur, conn)
            elif choice == "5":  menu_move_group(cur, conn)
            elif choice == "6":  menu_bulk(cur, conn)
            elif choice == "7":  menu_delete(cur, conn)
            elif choice == "8":  menu_export_json(cur)
            elif choice == "9":  menu_import_json(cur, conn)
            elif choice == "10": menu_import_csv(cur, conn)
            elif choice == "0":  break
            else:                print("  Неверный выбор.")
        except Exception as e:
            conn.rollback()
            print(f"  Ошибка: {e}")

    cur.close()
    conn.close()
    print("До свидания!")


if __name__ == "__main__":
    main()
