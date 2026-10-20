"""Các route của Guestbook."""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from .stats import count_by_sender, render_bar_chart
from .storage import STORAGE_KEY, SqliteStorage

bp = Blueprint("guestbook", __name__)


def get_storage() -> SqliteStorage:
    return current_app.extensions[STORAGE_KEY]


def validate(name: str, message: str) -> str | None:
    """Trả về thông báo lỗi, hoặc None nếu dữ liệu hợp lệ."""
    if not name or not message:
        return "Vui lòng nhập đầy đủ tên và lời nhắn."
    if len(name) > current_app.config["MAX_NAME_LENGTH"]:
        return f"Tên tối đa {current_app.config['MAX_NAME_LENGTH']} ký tự."
    if len(message) > current_app.config["MAX_MESSAGE_LENGTH"]:
        return f"Lời nhắn tối đa {current_app.config['MAX_MESSAGE_LENGTH']} ký tự."
    return None


@bp.get("/")
def index():
    entries = get_storage().all()
    return render_template("index.html", entries=list(reversed(entries)))


@bp.route("/add", methods=["GET", "POST"])
def add():
    name = request.form.get("name", "").strip()
    message = request.form.get("message", "").strip()

    if request.method == "POST":
        error = validate(name, message)
        if error is None:
            entry = get_storage().add(name, message)
            flash(f"Đã thêm lời nhắn #{entry.id}.", "success")
            return redirect(url_for(".index"))
        return render_template("add.html", error=error, name=name, message=message), 400

    return render_template("add.html", error=None, name=name, message=message)


@bp.post("/delete/<int:entry_id>")
def delete(entry_id: int):
    if get_storage().delete(entry_id):
        flash(f"Đã xóa lời nhắn #{entry_id}.", "success")
    else:
        flash(f"Không tìm thấy lời nhắn #{entry_id}.", "error")
    return redirect(url_for(".index"))


@bp.get("/stats")
def stats():
    entries = get_storage().all()
    counts = count_by_sender(entries)
    top_n = current_app.config["TOP_SENDERS"]

    chart_file = Path(current_app.config["CHART_FILE"])
    has_chart = render_bar_chart(counts, chart_file)

    return render_template(
        "stats.html",
        total=len(entries),
        senders=len(counts),
        top=counts.most_common(top_n),
        top_n=top_n,
        has_chart=has_chart,
        # đổi URL mỗi lần vẽ lại để trình duyệt không dùng ảnh cũ trong cache
        chart_version=chart_file.stat().st_mtime_ns if has_chart else 0,
    )
