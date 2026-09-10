import os
import psycopg2
import psycopg2.extras


def get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS main_categories (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    sort_order INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sub_categories (
    id SERIAL PRIMARY KEY,
    main_category_id INT NOT NULL REFERENCES main_categories(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    sort_order INT DEFAULT 0,
    UNIQUE(main_category_id, name)
);

CREATE TABLE IF NOT EXISTS view_types (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    sort_order INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    sub_category_id INT NOT NULL REFERENCES sub_categories(id) ON DELETE CASCADE,
    view_type_id INT NOT NULL REFERENCES view_types(id),
    file_type TEXT NOT NULL,          -- 'pdf' or 'jpg'
    file_data BYTEA NOT NULL,         -- compressed file bytes
    original_size INT,
    compressed_size INT,
    uploaded_at TIMESTAMP DEFAULT NOW()
);
"""

SEED_MAIN = ["அரசு ஆணைகள்", "இயக்குநரின் ஆணைகள்", "நீதிமன்ற ஆணைகள்"]

SEED_SUB = {
    "அரசு ஆணைகள்": ["பொதுவானவை", "பொது நூலகத்துறை தொடர்பானவை"],
    "இயக்குநரின் ஆணைகள்": ["பொதுவானவை", "சம்மந்தப்பட்ட மாவட்டங்கள் தொடர்பானவை"],
    "நீதிமன்ற ஆணைகள்": ["பொதுவானவை", "பொது நூலகத்துறை தொடர்பானவை"],
}

SEED_VIEW_TYPES = [
    "பொதுவானவை",
    "மைய நூலகங்கள் தொடர்பானது",
    "கிளை நூலகங்கள் தொடர்பானது",
    "ஊரப்புற நூலகங்கள் தொடர்பானது",
    "அலுவலகம் தொடர்பானது",
]


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(SCHEMA_SQL)

    for i, name in enumerate(SEED_MAIN):
        cur.execute(
            "INSERT INTO main_categories (name, sort_order) VALUES (%s, %s) "
            "ON CONFLICT (name) DO NOTHING",
            (name, i),
        )
    conn.commit()

    cur.execute("SELECT id, name FROM main_categories")
    main_map = {name: mid for mid, name in cur.fetchall()}

    for main_name, subs in SEED_SUB.items():
        for j, sub_name in enumerate(subs):
            cur.execute(
                "INSERT INTO sub_categories (main_category_id, name, sort_order) "
                "VALUES (%s, %s, %s) ON CONFLICT (main_category_id, name) DO NOTHING",
                (main_map[main_name], sub_name, j),
            )
    conn.commit()

    for i, name in enumerate(SEED_VIEW_TYPES):
        cur.execute(
            "INSERT INTO view_types (name, sort_order) VALUES (%s, %s) "
            "ON CONFLICT (name) DO NOTHING",
            (name, i),
        )
    conn.commit()
    cur.close()
    conn.close()


def dict_cursor(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
