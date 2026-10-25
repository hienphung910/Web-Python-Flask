import json
import os
import sqlite3
import time

import matplotlib
matplotlib.use("Agg")  # chỉ vẽ ra file ảnh, không mở cửa sổ
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

DB_FILE = os.path.join(app.root_path, "guestbook.db")
JSON_FILE = os.path.join(app.root_path, "data.json")
CHART_FILE = os.path.join(app.root_path, "static", "stats.png")


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


# Ghi toàn bộ lời nhắn ra data.json (gọi sau mỗi lần thêm/xóa)
def save_json():
    conn = get_db()
    rows = conn.execute("SELECT * FROM entries ORDER BY id").fetchall()
    conn.close()

    entries = []
    for row in rows:
        entries.append({"id": row["id"], "name": row["name"], "message": row["message"]})

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


# Khi khởi động: nếu database đang trống mà có data.json thì nạp dữ liệu từ file vào
def load_json():
    if not os.path.exists(JSON_FILE):
        return

    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
    if count == 0:
        with open(JSON_FILE, encoding="utf-8") as f:
            entries = json.load(f)
        for e in entries:
            # giữ nguyên id cũ để link xóa /delete/<id> vẫn đúng
            conn.execute(
                "INSERT INTO entries (id, name, message) VALUES (?, ?, ?)",
                (e["id"], e["name"], e["message"]),
            )
        conn.commit()
    conn.close()


init_db()
load_json()


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
    save_json()
    return redirect("/")


@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    conn = get_db()
    conn.execute("DELETE FROM entries WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    save_json()
    return redirect("/")


# Thống kê: tổng số lời nhắn, top 5 người gửi và biểu đồ cột
@app.route("/stats")
def stats():
    # Đếm số lời nhắn của từng người, sắp xếp từ nhiều đến ít
    conn = get_db()
    rows = conn.execute("""
        SELECT name, COUNT(*) AS count
        FROM entries
        GROUP BY name
        ORDER BY count DESC, name
    """).fetchall()
    conn.close()

    total = 0
    for row in rows:
        total += row["count"]

    top5 = rows[:5]

    # Vẽ biểu đồ cột rồi lưu vào static/stats.png
    if total > 0:
        names = []
        counts = []
        for row in rows:
            names.append(row["name"])
            counts.append(row["count"])

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(names, counts, color="#2a78d6")
        ax.set_title("Số lời nhắn theo người gửi")
        ax.set_xlabel("Người gửi")
        ax.set_ylabel("Số lời nhắn")
        ax.yaxis.get_major_locator().set_params(integer=True)  # trục y chỉ hiện số nguyên
        fig.tight_layout()

        os.makedirs(os.path.dirname(CHART_FILE), exist_ok=True)
        fig.savefig(CHART_FILE)
        plt.close(fig)

    # Thêm ?v=... vào link ảnh để trình duyệt không dùng lại ảnh cũ đã lưu trong cache
    version = int(time.time())
    return render_template("stats.html", total=total, top5=top5, version=version)


if __name__ == "__main__":
    app.run(debug=True)
