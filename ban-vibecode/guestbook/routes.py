"""Các route của Guestbook."""

from __future__ import annotations

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from . import storage

bp = Blueprint("guestbook", __name__)


def validate(name: str, message: str) -> dict[str, str]:
    """Kiểm tra form, trả về {tên trường: thông báo lỗi}. Rỗng nghĩa là hợp lệ."""
    errors = {}
    max_name = current_app.config["MAX_NAME_LENGTH"]
    max_message = current_app.config["MAX_MESSAGE_LENGTH"]

    if not name:
        errors["name"] = "Vui lòng nhập tên của bạn."
    elif len(name) > max_name:
        errors["name"] = f"Tên tối đa {max_name} ký tự."

    if not message:
        errors["message"] = "Vui lòng nhập lời nhắn."
    elif len(message) > max_message:
        errors["message"] = f"Lời nhắn tối đa {max_message} ký tự."

    return errors


@bp.get("/")
def index():
    # Lời nhắn mới nhất hiện trước
    entries = list(reversed(storage.list_entries()))
    return render_template("index.html", entries=entries)


@bp.route("/add", methods=["GET", "POST"])
def add():
    name = request.form.get("name", "").strip()
    message = request.form.get("message", "").strip()

    if request.method == "POST":
        errors = validate(name, message)
        if not errors:
            entry = storage.add_entry(name, message)
            flash(f"Đã thêm lời nhắn #{entry.id}. Cảm ơn {name}!", "success")
            return redirect(url_for(".index"))
        return render_template("add.html", errors=errors, name=name, message=message), 400

    return render_template("add.html", errors={}, name=name, message=message)


@bp.post("/delete/<int:entry_id>")
def delete(entry_id: int):
    if storage.delete_entry(entry_id):
        flash(f"Đã xóa lời nhắn #{entry_id}.", "success")
    else:
        flash(f"Không tìm thấy lời nhắn #{entry_id}.", "error")
    return redirect(url_for(".index"))
