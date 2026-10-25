"""Lưu trữ lời nhắn trong SQLite, kèm bản sao JSON.

Mỗi request mở một kết nối riêng (giữ trong `g`) và đóng khi request kết thúc, nên
không cần lock: SQLite tự xử lý việc nhiều request ghi cùng lúc.

SQLite là nơi lưu chính. Sau mỗi lần thêm/xóa, toàn bộ lời nhắn được ghi ra file JSON
(`DATA_FILE`); khi khởi động mà database còn trống thì dữ liệu được nạp lại từ file đó.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, current_app, g

from .models import Entry, SenderStat

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
    """Tạo bảng, nạp dữ liệu từ JSON nếu database trống, đăng ký đóng kết nối."""
    db = sqlite3.connect(app.config["DATABASE"])
    db.execute(SCHEMA)
    _import_json(db, Path(app.config["DATA_FILE"]))
    db.commit()
    db.close()
    app.teardown_appcontext(close_db)


def _import_json(db: sqlite3.Connection, path: Path) -> None:
    """Nạp lời nhắn từ file JSON vào bảng đang trống, giữ nguyên ID cũ."""
    if not path.exists() or db.execute("SELECT 1 FROM entries LIMIT 1").fetchone():
        return
    items = json.loads(path.read_text(encoding="utf-8"))
    db.executemany(
        "INSERT INTO entries (id, name, message, created_at) VALUES (:id, :name, :message, :created_at)",
        items,
    )


def _export_json() -> None:
    """Ghi toàn bộ lời nhắn ra file JSON.

    Ghi vào file tạm rồi đổi tên, nên nếu chương trình dừng giữa chừng thì file cũ vẫn nguyên vẹn.
    """
    path = Path(current_app.config["DATA_FILE"])
    items = [
        {"id": e.id, "name": e.name, "message": e.message, "created_at": e.created_iso}
        for e in list_entries()
    ]
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


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
    _export_json()
    return Entry(cursor.lastrowid, name, message, created_at)


def delete_entry(entry_id: int) -> bool:
    """Xóa theo ID. Trả về False nếu không tìm thấy."""
    db = get_db()
    cursor = db.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    db.commit()
    if cursor.rowcount == 0:
        return False
    _export_json()
    return True


def count_by_name() -> list[SenderStat]:
    """Số lời nhắn của từng người gửi, nhiều nhất trước (bằng nhau thì xếp theo tên)."""
    rows = get_db().execute(
        "SELECT name, COUNT(*) AS n FROM entries GROUP BY name ORDER BY n DESC, name"
    ).fetchall()
    return [SenderStat(row["name"], row["n"]) for row in rows]
