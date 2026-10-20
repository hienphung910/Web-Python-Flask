"""Lưu trữ lời nhắn trong một list Python toàn cục (dữ liệu nằm trong bộ nhớ).

Dữ liệu mất khi tắt chương trình. Các thao tác được bọc trong lock vì Flask có thể
xử lý nhiều request cùng lúc trên nhiều thread.
"""

from __future__ import annotations

import itertools
import threading

from .models import Entry

# List toàn cục chứa tất cả lời nhắn, theo thứ tự thêm vào
entries: list[Entry] = []

_ids = itertools.count(1)  # cấp ID tăng dần, ID đã xóa không bao giờ được dùng lại
_lock = threading.Lock()


def list_entries() -> list[Entry]:
    """Trả về bản sao của list để nơi gọi không vô tình sửa dữ liệu gốc."""
    with _lock:
        return list(entries)


def add_entry(name: str, message: str) -> Entry:
    with _lock:
        entry = Entry(next(_ids), name, message)
        entries.append(entry)
        return entry


def delete_entry(entry_id: int) -> bool:
    """Xóa theo ID. Trả về False nếu không tìm thấy."""
    with _lock:
        for index, entry in enumerate(entries):
            if entry.id == entry_id:
                del entries[index]
                return True
        return False


def reset() -> None:
    """Xóa sạch dữ liệu và đếm lại ID từ 1 (dùng trong test)."""
    global _ids
    with _lock:
        entries.clear()
        _ids = itertools.count(1)
