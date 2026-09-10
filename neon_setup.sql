-- இதை அப்படியே காபி பண்ணி Neon Console -> SQL Editor -ல் paste பண்ணி Run பண்ணவும்

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
    file_type TEXT NOT NULL,
    file_data BYTEA NOT NULL,
    original_size INT,
    compressed_size INT,
    uploaded_at TIMESTAMP DEFAULT NOW()
);

-- முதன்மை வகைகள் (3)
INSERT INTO main_categories (name, sort_order) VALUES
  ('அரசு ஆணைகள்', 0),
  ('இயக்குநரின் ஆணைகள்', 1),
  ('நீதிமன்ற ஆணைகள்', 2)
ON CONFLICT (name) DO NOTHING;

-- துணை வகைகள்
INSERT INTO sub_categories (main_category_id, name, sort_order)
SELECT id, 'பொதுவானவை', 0 FROM main_categories WHERE name = 'அரசு ஆணைகள்'
ON CONFLICT (main_category_id, name) DO NOTHING;

INSERT INTO sub_categories (main_category_id, name, sort_order)
SELECT id, 'பொது நூலகத்துறை தொடர்பானவை', 1 FROM main_categories WHERE name = 'அரசு ஆணைகள்'
ON CONFLICT (main_category_id, name) DO NOTHING;

INSERT INTO sub_categories (main_category_id, name, sort_order)
SELECT id, 'பொதுவானவை', 0 FROM main_categories WHERE name = 'இயக்குநரின் ஆணைகள்'
ON CONFLICT (main_category_id, name) DO NOTHING;

INSERT INTO sub_categories (main_category_id, name, sort_order)
SELECT id, 'சம்மந்தப்பட்ட மாவட்டங்கள் தொடர்பானவை', 1 FROM main_categories WHERE name = 'இயக்குநரின் ஆணைகள்'
ON CONFLICT (main_category_id, name) DO NOTHING;

INSERT INTO sub_categories (main_category_id, name, sort_order)
SELECT id, 'பொதுவானவை', 0 FROM main_categories WHERE name = 'நீதிமன்ற ஆணைகள்'
ON CONFLICT (main_category_id, name) DO NOTHING;

INSERT INTO sub_categories (main_category_id, name, sort_order)
SELECT id, 'பொது நூலகத்துறை தொடர்பானவை', 1 FROM main_categories WHERE name = 'நீதிமன்ற ஆணைகள்'
ON CONFLICT (main_category_id, name) DO NOTHING;

-- ஆவணப் பார்வை முறைகள்
INSERT INTO view_types (name, sort_order) VALUES
  ('பொதுவானவை', 0),
  ('மைய நூலகங்கள் தொடர்பானது', 1),
  ('கிளை நூலகங்கள் தொடர்பானது', 2),
  ('ஊரப்புற நூலகங்கள் தொடர்பானது', 3),
  ('அலுவலகம் தொடர்பானது', 4)
ON CONFLICT (name) DO NOTHING;

-- சரிபார்க்க
SELECT * FROM main_categories;
SELECT * FROM sub_categories;
SELECT * FROM view_types;
