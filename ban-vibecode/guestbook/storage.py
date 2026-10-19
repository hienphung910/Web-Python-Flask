"""Lưu trữ lời nhắn trong cơ sở dữ liệu MySQL."""

from __future__ import annotations

import logging
import os
import tempfile
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import pymysql
import pymysql.cursors

from .models import Entry

logger = logging.getLogger(__name__)

# Khóa để gắn storage vào app.extensions
STORAGE_KEY = "guestbook_storage"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS entries (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    message    TEXT NOT NULL,
    created_at DATETIME NOT NULL
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


class MysqlStorage:
    """Lời nhắn được lưu trong bảng ``entries`` của một database MySQL.

    Mỗi thao tác mở một kết nối riêng (kết nối PyMySQL không dùng chung được giữa
    các thread), và được bọc trong lock để các request thêm/xóa chạy tuần tự.
    ID do MySQL cấp (AUTO_INCREMENT) nên ID đã xóa không bao giờ được dùng lại.
    """

    def __init__(self, host: str, port: int, user: str, password: str, database: str) -> None:
        self._conn_args = dict(
            host=host,
            port=port,
            user=user,
            password=password,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
        self._database = database
        self._lock = threading.Lock()
        self._init_db()
        logger.info("Dùng MySQL %s@%s:%s, database %s", user, host, port, database)

    def _init_db(self) -> None:
        """Tạo database và bảng nếu chưa có."""
        conn = pymysql.connect(**self._conn_args)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{self._database}` CHARACTER SET utf8mb4"
                )
        finally:
            conn.close()
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)

    @contextmanager
    def _connect(self) -> Iterator[pymysql.connections.Connection]:
        """Mở kết nối, commit khi xong (rollback nếu lỗi) rồi đóng lại."""
        conn = pymysql.connect(**self._conn_args, database=self._database)
        try:
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def _to_entry(row: dict) -> Entry:
        created = row["created_at"]
        if isinstance(created, datetime):
            created = created.isoformat(timespec="seconds")
        return Entry(int(row["id"]), row["name"], row["message"], str(created))

    def all(self) -> list[Entry]:
        with self._lock, self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT id, name, message, created_at FROM entries ORDER BY id")
            return [self._to_entry(row) for row in cur.fetchall()]

    def add(self, name: str, message: str) -> Entry:
        created = datetime.now().replace(microsecond=0)
        with self._lock, self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO entries (name, message, created_at) VALUES (%s, %s, %s)",
                (name, message, created),
            )
            return Entry(cur.lastrowid, name, message, created.isoformat(timespec="seconds"))

    def delete(self, entry_id: int) -> bool:
        """Xóa theo ID. Trả về False nếu không tìm thấy."""
        with self._lock, self._connect() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM entries WHERE id = %s", (entry_id,))
            return cur.rowcount > 0
