"""Lưu trữ lời nhắn trong bộ nhớ, đồng bộ xuống file JSON."""

from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
from pathlib import Path

from .models import Entry

logger = logging.getLogger(__name__)

# Khóa để gắn JsonStorage vào app.extensions
STORAGE_KEY = "guestbook_storage"


def atomic_write(path: Path, data: bytes) -> None:
    """Ghi file kiểu "tất cả hoặc không": ghi ra file tạm rồi đổi tên.

    Nếu chương trình dừng giữa chừng, file cũ vẫn còn nguyên, không bị hỏng một nửa.
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


class JsonStorage:
    """Danh sách lời nhắn (list Python) được nạp từ và ghi lại vào file JSON.

    Dùng lock vì Flask có thể xử lý nhiều request cùng lúc trên nhiều thread.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._entries: list[Entry] = self._load()

    def _load(self) -> list[Entry]:
        if not self._path.exists():
            return []
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            return [Entry.from_dict(item) for item in raw]
        except (OSError, ValueError, KeyError, TypeError) as exc:
            logger.warning("Không đọc được %s (%s), bắt đầu với dữ liệu rỗng", self._path, exc)
            return []

    def _save(self) -> None:
        payload = json.dumps([e.to_dict() for e in self._entries], ensure_ascii=False, indent=2)
        atomic_write(self._path, payload.encode("utf-8"))

    def all(self) -> list[Entry]:
        with self._lock:
            return list(self._entries)

    def add(self, name: str, message: str) -> Entry:
        with self._lock:
            next_id = max((e.id for e in self._entries), default=0) + 1
            entry = Entry.create(next_id, name, message)
            self._entries.append(entry)
            self._save()
            return entry

    def delete(self, entry_id: int) -> bool:
        """Xóa theo ID. Trả về False nếu không tìm thấy."""
        with self._lock:
            remaining = [e for e in self._entries if e.id != entry_id]
            if len(remaining) == len(self._entries):
                return False
            self._entries = remaining
            self._save()
            return True
