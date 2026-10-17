import json
import os

import matplotlib
matplotlib.use("Agg")  # vẽ biểu đồ ra file, không mở cửa sổ
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

DATA_FILE = "data.json"


# Đọc dữ liệu từ file JSON, nếu chưa có file thì trả về list rỗng
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


# Ghi list lời nhắn ra file JSON
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


# List toàn cục chứa các lời nhắn, mỗi lời nhắn là 1 dict: {"id", "name", "message"}
entries = load_data()


# Trang chủ: hiển thị tất cả lời nhắn
@app.route("/")
def index():
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

    # Tạo id mới = id lớn nhất + 1
    new_id = 1
    for e in entries:
        if e["id"] >= new_id:
            new_id = e["id"] + 1

    entries.append({"id": new_id, "name": name, "message": message})
    save_data()
    return redirect("/")


# Xóa lời nhắn theo id
@app.route("/delete/<int:id>", methods=["GET", "POST"])
def delete(id):
    for e in entries:
        if e["id"] == id:
            entries.remove(e)
            break
    save_data()
    return redirect("/")


# Thống kê
@app.route("/stats")
def stats():
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
