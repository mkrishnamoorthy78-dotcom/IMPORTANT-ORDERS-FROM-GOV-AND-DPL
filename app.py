import os
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, send_file, jsonify, flash
)
from dotenv import load_dotenv
import io

from db import get_conn, dict_cursor, init_db
from compress import compress_file

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 MB upload limit

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Dlodgl@789")

# Auto-create tables on every startup (safe to run repeatedly - uses
# ON CONFLICT DO NOTHING). This removes the need for Shell access,
# which is not available on Render's free plan.
try:
    init_db()
except Exception as e:
    print(f"init_db() warning: {e}")


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper


# ---------- Public viewer routes ----------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/categories")
def api_categories():
    conn = get_conn()
    cur = dict_cursor(conn)
    cur.execute("SELECT id, name FROM main_categories ORDER BY sort_order, id")
    mains = cur.fetchall()
    for m in mains:
        cur.execute(
            "SELECT id, name FROM sub_categories WHERE main_category_id=%s "
            "ORDER BY sort_order, id",
            (m["id"],),
        )
        m["sub_categories"] = cur.fetchall()
    cur.execute("SELECT id, name FROM view_types ORDER BY sort_order, id")
    view_types = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify({"main_categories": mains, "view_types": view_types})


@app.route("/api/orders")
def api_orders():
    sub_category_id = request.args.get("sub_category_id", type=int)
    view_type_id = request.args.get("view_type_id", type=int)

    query = (
        "SELECT o.id, o.title, o.file_type, o.uploaded_at, "
        "sc.name AS sub_category, mc.name AS main_category, vt.name AS view_type "
        "FROM orders o "
        "JOIN sub_categories sc ON o.sub_category_id = sc.id "
        "JOIN main_categories mc ON sc.main_category_id = mc.id "
        "JOIN view_types vt ON o.view_type_id = vt.id "
        "WHERE 1=1"
    )
    params = []
    if sub_category_id:
        query += " AND o.sub_category_id = %s"
        params.append(sub_category_id)
    if view_type_id:
        query += " AND o.view_type_id = %s"
        params.append(view_type_id)
    query += " ORDER BY o.uploaded_at DESC"

    conn = get_conn()
    cur = dict_cursor(conn)
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows)


@app.route("/view/<int:order_id>")
def view_order(order_id):
    conn = get_conn()
    cur = dict_cursor(conn)
    cur.execute("SELECT file_data, file_type, title FROM orders WHERE id=%s", (order_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return "கிடைக்கவில்லை", 404
    mimetype = "application/pdf" if row["file_type"] == "pdf" else "image/jpeg"
    return send_file(
        io.BytesIO(bytes(row["file_data"])),
        mimetype=mimetype,
        download_name=f"{row['title']}.{row['file_type']}",
    )


# ---------- Admin auth ----------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))
        flash("தவறான கடவுச்சொல்")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("index"))


# ---------- Admin dashboard ----------

@app.route("/admin")
@admin_required
def admin_dashboard():
    return render_template("admin.html")


@app.route("/admin/category/add_main", methods=["POST"])
@admin_required
def add_main_category():
    name = request.form.get("name", "").strip()
    if name:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO main_categories (name) VALUES (%s) ON CONFLICT DO NOTHING",
            (name,),
        )
        conn.commit()
        cur.close()
        conn.close()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/category/delete_main/<int:main_id>", methods=["POST"])
@admin_required
def delete_main_category(main_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM main_categories WHERE id=%s", (main_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/category/add_sub", methods=["POST"])
@admin_required
def add_sub_category():
    main_id = request.form.get("main_category_id", type=int)
    name = request.form.get("name", "").strip()
    if main_id and name:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO sub_categories (main_category_id, name) VALUES (%s, %s) "
            "ON CONFLICT DO NOTHING",
            (main_id, name),
        )
        conn.commit()
        cur.close()
        conn.close()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/category/delete_sub/<int:sub_id>", methods=["POST"])
@admin_required
def delete_sub_category(sub_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM sub_categories WHERE id=%s", (sub_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/upload", methods=["POST"])
@admin_required
def upload_order():
    title = request.form.get("title", "").strip()
    sub_category_id = request.form.get("sub_category_id", type=int)
    view_type_id = request.form.get("view_type_id", type=int)
    file = request.files.get("file")

    if not (title and sub_category_id and view_type_id and file):
        flash("அனைத்து புலங்களையும் நிரப்பவும்")
        return redirect(url_for("admin_dashboard"))

    original_bytes = file.read()
    ext = file.filename.rsplit(".", 1)[-1].lower()
    file_type = "pdf" if ext == "pdf" else "jpg"

    compressed_bytes = compress_file(original_bytes, file_type)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO orders (title, sub_category_id, view_type_id, file_type, "
        "file_data, original_size, compressed_size) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (
            title, sub_category_id, view_type_id, file_type,
            psycopg2_binary(compressed_bytes),
            len(original_bytes), len(compressed_bytes),
        ),
    )
    conn.commit()
    cur.close()
    conn.close()
    flash(f"பதிவேற்றம் வெற்றி: {len(original_bytes)//1024}KB -> {len(compressed_bytes)//1024}KB")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/order/delete/<int:order_id>", methods=["POST"])
@admin_required
def delete_order(order_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM orders WHERE id=%s", (order_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("admin_dashboard"))


def psycopg2_binary(data: bytes):
    import psycopg2
    return psycopg2.Binary(data)


@app.errorhandler(413)
def too_large(e):
    flash("கோப்பு அளவு 20 MB-க்கு மேல் இருக்கக்கூடாது")
    return redirect(url_for("admin_dashboard"))


@app.route("/healthz")
def healthz():
    return "ok"


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
