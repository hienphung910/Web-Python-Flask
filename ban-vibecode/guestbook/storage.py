"""Lưu trữ lời nhắn trong SQLite.

Mỗi request mở một kết nối riêng (giữ trong `g`) và đóng khi request kết thúc, nên
không cần lock: SQLite tự xử lý việc nhiều request ghi cùng lúc.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime

from flask import Flask, current_app, g

from .models import Entry

# AUTOINCREMENT để ID đã xóa không bao giờ được cấp lại
SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""


def get_db() -> sqlite3.Connection:
    """Kết nối của request hiện tại, mở khi cần lần đầu."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exc: BaseException | None = None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app: Flask) -> None:
    """Tạo bảng nếu chưa có và đăng ký đóng kết nối sau mỗi request."""
    db = sqlite3.connect(app.config["DATABASE"])
    db.execute(SCHEMA)
    db.commit()
    db.close()
    app.teardown_appcontext(close_db)


def _to_entry(row: sqlite3.Row) -> Entry:
    return Entry(row["id"], row["name"], row["message"], datetime.fromisoformat(row["created_at"]))


def list_entries() -> list[Entry]:
    """Tất cả lời nhắn, theo thứ tự thêm vào."""
    rows = get_db().execute("SELECT * FROM entries ORDER BY id").fetchall()
    return [_to_entry(row) for row in rows]


def add_entry(name: str, message: str) -> Entry:
    created_at = datetime.now().replace(microsecond=0)
    db = get_db()
    cursor = db.execute(
        "INSERT INTO entries (name, message, created_at) VALUES (?, ?, ?)",
        (name, message, created_at.isoformat()),
    )
    db.commit()
    return Entry(cursor.lastrowid, name, message, created_at)


def delete_entry(entry_id: int) -> bool:
    """Xóa theo ID. Trả về False nếu không tìm thấy."""
    db = get_db()
    cursor = db.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    db.commit()
    return cursor.rowcount > 0
