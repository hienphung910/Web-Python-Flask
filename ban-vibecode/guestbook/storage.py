"""Lưu trữ lời nhắn trong cơ sở dữ liệu SQLite."""

from __future__ import annotations

import logging
import os
import sqlite3
import tempfile
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from .models import Entry

logger = logging.getLogger(__name__)

# Khóa để gắn storage vào app.extensions
STORAGE_KEY = "guestbook_storage"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS entries (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    message    TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""


def atomic_write(path: Path, data: bytes) -> None:
    """Ghi file kiểu "tất cả hoặc không": ghi ra file tạm rồi đổi tên.

    Nếu chương trình dừng giữa chừng, file cũ vẫn còn nguyên, không bị hỏng một nửa.
    Dùng cho file ảnh biểu đồ.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as tmp:
            tmp.write(data)
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


class SqliteStorage:
    """Lời nhắn được lưu trong bảng ``entries`` của một file SQLite.

    Mỗi thao tác mở một kết nối riêng (mặc định kết nối sqlite3 không dùng chung
    được giữa các thread), và được bọc trong lock để các request thêm/xóa chạy tuần tự.
    ID do SQLite cấp (AUTOINCREMENT) nên ID đã xóa không bao giờ được dùng lại.
    """

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._lock = threading.Lock()
        self._init_db()
        logger.info("Dùng SQLite %s", self._path)

    def _init_db(self) -> None:
        """Tạo thư mục chứa file DB và bảng nếu chưa có."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(CREATE_TABLE_SQL)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Mở kết nối, commit khi xong (rollback nếu lỗi) rồi đóng lại."""
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def _to_entry(row: sqlite3.Row) -> Entry:
        return Entry(int(row["id"]), row["name"], row["message"], row["created_at"])

    def all(self) -> list[Entry]:
        with self._lock, self._connect() as conn:
            rows = conn.execute("SELECT id, name, message, created_at FROM entries ORDER BY id")
            return [self._to_entry(row) for row in rows]

    def add(self, name: str, message: str) -> Entry:
        created = datetime.now().isoformat(timespec="seconds")
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO entries (name, message, created_at) VALUES (?, ?, ?)",
                (name, message, created),
            )
            return Entry(cur.lastrowid, name, message, created)

    def delete(self, entry_id: int) -> bool:
        """Xóa theo ID. Trả về False nếu không tìm thấy."""
        with self._lock, self._connect() as conn:
            cur = conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
            return cur.rowcount > 0
