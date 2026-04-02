
CREATE OR REPLACE PROCEDURE upsert_contact(p_name VARCHAR, p_phone VARCHAR)
LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM contacts WHERE name = p_name) THEN
        UPDATE contacts SET phone_number = p_phone WHERE name = p_name;
    ELSE
        INSERT INTO contacts(name, phone_number)
        VALUES(p_name, p_phone);
    END IF;
END;
$$;


CREATE OR REPLACE PROCEDURE bulk_insert_contacts(
    p_names TEXT[],
    p_phones TEXT[]
)
LANGUAGE plpgsql AS $$
DECLARE
    i INT;
BEGIN
    FOR i IN 1..array_length(p_names, 1) LOOP
        
        IF p_phones[i] ~ '^[0-9]+$' THEN
            INSERT INTO contacts(name, phone_number)
            VALUES(p_names[i], p_phones[i]);
        ELSE
            RAISE NOTICE 'Invalid phone for %: %', p_names[i], p_phones[i];
        END IF;

    END LOOP;
END;
$$;

CREATE OR REPLACE PROCEDURE delete_contact(p_value TEXT)
LANGUAGE plpgsql AS $$
BEGIN
    DELETE FROM contacts
    WHERE name = p_value OR phone_number = p_value;
END;
$$;