import os
import sqlite3

from flask import Flask, render_template, request, redirect

app = Flask(__name__)

DB_FILE = os.path.join(app.root_path, "guestbook.db")


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # lấy cột theo tên: row["name"]
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


init_db()


# Trang chủ: hiển thị tất cả lời nhắn
@app.route("/")
def index():
    conn = get_db()
    entries = conn.execute("SELECT * FROM entries ORDER BY id").fetchall()
    conn.close()
    return render_template("index.html", entries=entries)


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "GET":
        return render_template("add.html", error="", name="", message="")

    name = request.form["name"].strip()
    message = request.form["message"].strip()

    if name == "" or message == "":
        error = "Không được để trống tên và lời nhắn!"
        return render_template("add.html", error=error, name=name, message=message)

    conn = get_db()
    conn.execute("INSERT INTO entries (name, message) VALUES (?, ?)", (name, message))
    conn.commit()
    conn.close()
    return redirect("/")


@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    conn = get_db()
    conn.execute("DELETE FROM entries WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
