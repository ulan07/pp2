-- ============================================================
--  PHONEBOOK  —  Stored Procedures & Functions
-- ============================================================

-- ------------------------------------------------------------
-- 1. Upsert contact  (name is unique key)
-- ------------------------------------------------------------
CREATE OR REPLACE PROCEDURE upsert_contact(
    p_name    VARCHAR,
    p_email   VARCHAR DEFAULT NULL,
    p_bday    DATE    DEFAULT NULL,
    p_group   VARCHAR DEFAULT NULL,
    p_phone   VARCHAR DEFAULT NULL,
    p_type    VARCHAR DEFAULT 'mobile'
)
LANGUAGE plpgsql AS $$
DECLARE
    v_group_id   INTEGER;
    v_contact_id INTEGER;
BEGIN
    IF p_group IS NOT NULL THEN
        SELECT id INTO v_group_id FROM groups WHERE name ILIKE p_group LIMIT 1;
        IF v_group_id IS NULL THEN
            INSERT INTO groups(name) VALUES(p_group) RETURNING id INTO v_group_id;
        END IF;
    END IF;

    SELECT id INTO v_contact_id FROM contacts WHERE name = p_name;
    IF v_contact_id IS NOT NULL THEN
        UPDATE contacts
           SET email    = COALESCE(p_email, email),
               birthday = COALESCE(p_bday,  birthday),
               group_id = COALESCE(v_group_id, group_id)
         WHERE id = v_contact_id;
    ELSE
        INSERT INTO contacts(name, email, birthday, group_id)
        VALUES(p_name, p_email, p_bday, v_group_id)
        RETURNING id INTO v_contact_id;
    END IF;

    IF p_phone IS NOT NULL THEN
        INSERT INTO phones(contact_id, phone, type)
        VALUES(v_contact_id, p_phone, p_type);
    END IF;
END;
$$;

-- ------------------------------------------------------------
-- 2. Add phone number to existing contact
-- ------------------------------------------------------------
CREATE OR REPLACE PROCEDURE add_phone(
    p_contact_name VARCHAR,
    p_phone        VARCHAR,
    p_type         VARCHAR DEFAULT 'mobile'
)
LANGUAGE plpgsql AS $$
DECLARE
    v_id INTEGER;
BEGIN
    SELECT id INTO v_id FROM contacts WHERE name = p_contact_name LIMIT 1;
    IF v_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found', p_contact_name;
    END IF;
    INSERT INTO phones(contact_id, phone, type) VALUES(v_id, p_phone, p_type);
END;
$$;

-- ------------------------------------------------------------
-- 3. Move contact to group (create group if missing)
-- ------------------------------------------------------------
CREATE OR REPLACE PROCEDURE move_to_group(
    p_contact_name VARCHAR,
    p_group_name   VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_group_id   INTEGER;
    v_contact_id INTEGER;
BEGIN
    SELECT id INTO v_group_id FROM groups WHERE name ILIKE p_group_name LIMIT 1;
    IF v_group_id IS NULL THEN
        INSERT INTO groups(name) VALUES(p_group_name) RETURNING id INTO v_group_id;
    END IF;

    SELECT id INTO v_contact_id FROM contacts WHERE name = p_contact_name LIMIT 1;
    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found', p_contact_name;
    END IF;

    UPDATE contacts SET group_id = v_group_id WHERE id = v_contact_id;
END;
$$;

-- ------------------------------------------------------------
-- 4. Bulk insert contacts
-- ------------------------------------------------------------
CREATE OR REPLACE PROCEDURE bulk_insert_contacts(
    p_names  TEXT[],
    p_phones TEXT[],
    p_types  TEXT[] DEFAULT NULL
)
LANGUAGE plpgsql AS $$
DECLARE
    i   INT;
    v_id INTEGER;
    v_type TEXT;
BEGIN
    FOR i IN 1..array_length(p_names, 1) LOOP
        IF p_phones[i] ~ '^\+?[0-9\s\-]+$' THEN
            SELECT id INTO v_id FROM contacts WHERE name = p_names[i];
            IF v_id IS NULL THEN
                INSERT INTO contacts(name) VALUES(p_names[i]) RETURNING id INTO v_id;
            END IF;
            v_type := COALESCE(p_types[i], 'mobile');
            INSERT INTO phones(contact_id, phone, type) VALUES(v_id, p_phones[i], v_type);
        ELSE
            RAISE NOTICE 'Invalid phone for %: %', p_names[i], p_phones[i];
        END IF;
    END LOOP;
END;
$$;

-- ------------------------------------------------------------
-- 5. Delete contact by name or phone
-- ------------------------------------------------------------
CREATE OR REPLACE PROCEDURE delete_contact(p_value TEXT)
LANGUAGE plpgsql AS $$
BEGIN
    DELETE FROM contacts
     WHERE name = p_value
        OR id IN (SELECT contact_id FROM phones WHERE phone = p_value);
END;
$$;

-- ============================================================
--  FUNCTIONS
-- ============================================================

-- ------------------------------------------------------------
-- 6. Search contacts (name + email + all phones)
-- ------------------------------------------------------------
CREATE OR REPLACE FUNCTION search_contacts(p_query TEXT)
RETURNS TABLE(
    id       INT,
    name     VARCHAR,
    email    VARCHAR,
    birthday DATE,
    grp      VARCHAR,
    phones   TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT
        c.id,
        c.name,
        c.email,
        c.birthday,
        g.name  AS grp,
        STRING_AGG(p.phone || ' (' || COALESCE(p.type,'?') || ')', ', ')
            OVER (PARTITION BY c.id) AS phones
    FROM contacts c
    LEFT JOIN groups g ON g.id = c.group_id
    LEFT JOIN phones p ON p.contact_id = c.id
    WHERE c.name  ILIKE '%' || p_query || '%'
       OR c.email ILIKE '%' || p_query || '%'
       OR p.phone ILIKE '%' || p_query || '%'
    ORDER BY c.name;
END;
$$ LANGUAGE plpgsql;

-- ------------------------------------------------------------
-- 7. Paginated contact list
-- ------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_contacts_paginated(
    p_limit    INT,
    p_offset   INT,
    p_sort     VARCHAR DEFAULT 'name',   -- name | birthday | created_at
    p_group_id INT     DEFAULT NULL
)
RETURNS TABLE(
    id       INT,
    name     VARCHAR,
    email    VARCHAR,
    birthday DATE,
    grp      VARCHAR,
    phones   TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT
        c.id,
        c.name,
        c.email,
        c.birthday,
        g.name AS grp,
        STRING_AGG(ph.phone || ' (' || COALESCE(ph.type,'?') || ')', ', ')
            OVER (PARTITION BY c.id) AS phones
    FROM contacts c
    LEFT JOIN groups g  ON g.id  = c.group_id
    LEFT JOIN phones ph ON ph.contact_id = c.id
    WHERE (p_group_id IS NULL OR c.group_id = p_group_id)
    ORDER BY
        CASE WHEN p_sort = 'birthday'   THEN c.birthday::TEXT   END,
        CASE WHEN p_sort = 'created_at' THEN c.created_at::TEXT END,
        c.name
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- ------------------------------------------------------------
-- 8. Filter by group name
-- ------------------------------------------------------------
CREATE OR REPLACE FUNCTION filter_by_group(p_group_name VARCHAR)
RETURNS TABLE(
    id       INT,
    name     VARCHAR,
    email    VARCHAR,
    birthday DATE,
    phones   TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT
        c.id,
        c.name,
        c.email,
        c.birthday,
        STRING_AGG(p.phone || ' (' || COALESCE(p.type,'?') || ')', ', ')
            OVER (PARTITION BY c.id) AS phones
    FROM contacts c
    JOIN groups g ON g.id = c.group_id
    LEFT JOIN phones p ON p.contact_id = c.id
    WHERE g.name ILIKE p_group_name
    ORDER BY c.name;
END;
$$ LANGUAGE plpgsql;
