from datetime import datetime

import pymysql
import matplotlib
matplotlib.use("Agg")  # vẽ biểu đồ ra file, không mở cửa sổ
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, redirect

# Thông tin kết nối MySQL nằm trong db_config.py (xem db_config.example.py)
from db_config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

app = Flask(__name__)


# Mở kết nối tới MySQL. DictCursor để mỗi dòng kết quả là 1 dict: row["name"]
def get_db():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


# Tạo database và bảng entries nếu chưa có (chạy một lần khi khởi động)
def init_db():
    # Bước 1: kết nối chưa chọn database để tạo database
    conn = pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD)
    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4")
    conn.close()

    # Bước 2: tạo bảng trong database đó
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id         INT AUTO_INCREMENT PRIMARY KEY,
                name       VARCHAR(100) NOT NULL,
                message    TEXT NOT NULL,
                created_at DATETIME NOT NULL
            )
        """)
    conn.commit()
    conn.close()


# Lấy tất cả lời nhắn, mỗi dòng là 1 dict: {"id", "name", "message", "created_at"}
def get_all_entries():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM entries ORDER BY id")
        rows = cur.fetchall()
    conn.close()
    return rows


init_db()


# Trang chủ: hiển thị tất cả lời nhắn
@app.route("/")
def index():
    entries = get_all_entries()
    return render_template("index.html", entries=entries)


# Thêm lời nhắn
@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "GET":
        return render_template("add.html", error="", name="", message="")

    # POST: lấy dữ liệu từ form
    name = request.form["name"].strip()
    message = request.form["message"].strip()

    if name == "" or message == "":
        error = "Không được để trống tên và lời nhắn!"
        return render_template("add.html", error=error, name=name, message=message)

    # INSERT vào bảng; id do MySQL tự tăng (AUTO_INCREMENT)
    # %s là tham số, tránh lỗi SQL injection khi người dùng nhập ký tự lạ
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO entries (name, message, created_at) VALUES (%s, %s, %s)",
            (name, message, datetime.now()),
        )
    conn.commit()
    conn.close()
    return redirect("/")


# Xóa lời nhắn theo id
@app.route("/delete/<int:id>", methods=["GET", "POST"])
def delete(id):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM entries WHERE id = %s", (id,))
    conn.commit()
    conn.close()
    return redirect("/")


# Thống kê
@app.route("/stats")
def stats():
    entries = get_all_entries()
    total = len(entries)

    # Đếm số lời nhắn của từng người: {"An": 3, "Bình": 1, ...}
    counts = {}
    for e in entries:
        name = e["name"]
        if name in counts:
            counts[name] += 1
        else:
            counts[name] = 1

    # Sắp xếp giảm dần theo số lời nhắn rồi lấy 5 người đầu
    sorted_counts = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    top5 = sorted_counts[:5]

    # Vẽ biểu đồ cột và lưu vào static/stats.png
    if total > 0:
        names = []
        numbers = []
        for name, count in sorted_counts:
            names.append(name)
            numbers.append(count)

        plt.figure(figsize=(8, 4))
        plt.bar(names, numbers)
        plt.title("Số lời nhắn theo người gửi")
        plt.xlabel("Người gửi")
        plt.ylabel("Số lời nhắn")
        plt.tight_layout()
        plt.savefig("static/stats.png")
        plt.close()

    return render_template("stats.html", total=total, top5=top5)


if __name__ == "__main__":
    app.run(debug=True)
