from flask import Flask, render_template, request, redirect

app = Flask(__name__)

# Lưu trữ dữ liệu: list Python toàn cục, mỗi lời nhắn là 1 dict {"id", "name", "message"}
# Dữ liệu chỉ nằm trong bộ nhớ nên sẽ mất khi tắt chương trình
entries = []
next_id = 1  # id cấp cho lời nhắn tiếp theo, tăng dần, không dùng lại id đã xóa


# Trang chủ: hiển thị tất cả lời nhắn
@app.route("/")
def index():
    return render_template("index.html", entries=entries)


# Thêm lời nhắn
@app.route("/add", methods=["GET", "POST"])
def add():
    global next_id

    if request.method == "GET":
        return render_template("add.html", error="", name="", message="")

    # POST: lấy dữ liệu từ form
    name = request.form["name"].strip()
    message = request.form["message"].strip()

    if name == "" or message == "":
        error = "Không được để trống tên và lời nhắn!"
        return render_template("add.html", error=error, name=name, message=message)

    # Hợp lệ: thêm vào list rồi quay về trang chủ
    entries.append({"id": next_id, "name": name, "message": message})
    next_id += 1
    return redirect("/")


# Xóa lời nhắn theo id
@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    for e in entries:
        if e["id"] == id:
            entries.remove(e)
            break  # đã xóa xong, dừng vòng lặp
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
