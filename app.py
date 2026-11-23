import csv
import io
import os
import secrets
import sqlite3
from contextlib import closing
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    flash,
    g,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash


load_dotenv(Path(__file__).with_name(".env"))


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        DATABASE=os.path.join(app.instance_path, "contacts.sqlite3"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
        return g.db

    def init_db():
        with closing(sqlite3.connect(app.config["DATABASE"])) as db:
            db.execute("PRAGMA foreign_keys = ON")
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL DEFAULT '',
                    phone TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT ''
                );
                """
            )
            db.commit()

    init_db()

    @app.teardown_appcontext
    def close_db(_error=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    @app.before_request
    def protect_forms():
        session.setdefault("csrf_token", secrets.token_hex(32))
        if request.method == "POST":
            submitted = request.form.get("csrf_token", "")
            if not secrets.compare_digest(submitted, session["csrf_token"]):
                abort(400, description="Token de formulario no válido. Recarga la página.")

    def login_required(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            return view(**kwargs)

        return wrapped_view

    @app.route("/")
    @login_required
    def index():
        query = request.args.get("q", "").strip()
        contacts = get_db().execute(
            """
            SELECT id, name, email, phone, notes FROM contacts
            WHERE user_id = ? AND name LIKE ? ESCAPE '\\'
            ORDER BY name COLLATE NOCASE
            """,
            (session["user_id"], "%" + query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"),
        ).fetchall()
        return render_template("index.html", contacts=contacts, query=query)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            if not username or len(username) > 80:
                flash("El nombre de usuario es obligatorio (máximo 80 caracteres).", "error")
            elif len(password) < 8:
                flash("La contraseña debe tener al menos 8 caracteres.", "error")
            else:
                db = get_db()
                try:
                    cursor = db.execute(
                        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                        (username, generate_password_hash(password)),
                    )
                    db.commit()
                except sqlite3.IntegrityError:
                    flash("Ese nombre de usuario ya está en uso.", "error")
                else:
                    session.clear()
                    session["user_id"] = cursor.lastrowid
                    return redirect(url_for("index"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = get_db().execute(
                "SELECT id, password_hash FROM users WHERE username = ?", (username,)
            ).fetchone()
            if user is None or not check_password_hash(user["password_hash"], password):
                flash("Usuario o contraseña incorrectos.", "error")
            else:
                session.clear()
                session["user_id"] = user["id"]
                return redirect(url_for("index"))
        return render_template("login.html")

    @app.post("/logout")
    @login_required
    def logout():
        session.clear()
        return redirect(url_for("login"))

    def contact_for_user(contact_id):
        contact = get_db().execute(
            "SELECT * FROM contacts WHERE id = ? AND user_id = ?",
            (contact_id, session["user_id"]),
        ).fetchone()
        if contact is None:
            abort(404)
        return contact

    @app.route("/contacts/new", methods=["GET", "POST"])
    @login_required
    def add_contact():
        if request.method == "POST":
            values = {
                field: request.form.get(field, "").strip()
                for field in ("name", "email", "phone", "notes")
            }
            if not values["name"]:
                flash("El nombre es obligatorio.", "error")
            elif any(len(values[field]) > limit for field, limit in (
                ("name", 160), ("email", 254), ("phone", 40), ("notes", 2000)
            )):
                flash("Uno o más campos superan la longitud permitida.", "error")
            else:
                get_db().execute(
                    "INSERT INTO contacts (user_id, name, email, phone, notes) VALUES (?, ?, ?, ?, ?)",
                    (session["user_id"], values["name"], values["email"], values["phone"], values["notes"]),
                )
                get_db().commit()
                flash("Contacto guardado.", "success")
                return redirect(url_for("index"))
        return render_template("contact_form.html", contact=None)

    @app.route("/contacts/<int:contact_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_contact(contact_id):
        contact = contact_for_user(contact_id)
        if request.method == "POST":
            values = {
                field: request.form.get(field, "").strip()
                for field in ("name", "email", "phone", "notes")
            }
            if not values["name"]:
                flash("El nombre es obligatorio.", "error")
            elif any(len(values[field]) > limit for field, limit in (
                ("name", 160), ("email", 254), ("phone", 40), ("notes", 2000)
            )):
                flash("Uno o más campos superan la longitud permitida.", "error")
            else:
                get_db().execute(
                    """
                    UPDATE contacts SET name = ?, email = ?, phone = ?, notes = ?
                    WHERE id = ? AND user_id = ?
                    """,
                    (values["name"], values["email"], values["phone"], values["notes"],
                     contact_id, session["user_id"]),
                )
                get_db().commit()
                flash("Contacto actualizado.", "success")
                return redirect(url_for("index"))
        return render_template("contact_form.html", contact=contact)

    @app.post("/contacts/<int:contact_id>/delete")
    @login_required
    def delete_contact(contact_id):
        contact_for_user(contact_id)
        db = get_db()
        db.execute(
            "DELETE FROM contacts WHERE id = ? AND user_id = ?",
            (contact_id, session["user_id"]),
        )
        db.commit()
        flash("Contacto eliminado.", "success")
        return redirect(url_for("index"))

    def safe_csv_cell(value):
        value = value or ""
        if value.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")):
            return "'" + value
        return value

    @app.get("/export")
    @login_required
    def export_csv():
        rows = get_db().execute(
            """
            SELECT name, email, phone, notes FROM contacts
            WHERE user_id = ? ORDER BY name COLLATE NOCASE
            """,
            (session["user_id"],),
        ).fetchall()
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(("Nombre", "Correo electrónico", "Teléfono", "Notas"))
        for row in rows:
            writer.writerow([safe_csv_cell(row[field]) for field in ("name", "email", "phone", "notes")])
        response = make_response("\ufeff" + output.getvalue())
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        response.headers["Content-Disposition"] = "attachment; filename=contactos.csv"
        return response

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
