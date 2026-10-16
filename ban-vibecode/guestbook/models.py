"""Mô hình dữ liệu của một lời nhắn."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class Entry:
    id: int
    name: str
    message: str
    created_at: str  # ISO 8601, ví dụ "2026-10-16T23:33:00"

    @classmethod
    def create(cls, entry_id: int, name: str, message: str) -> Entry:
        return cls(entry_id, name, message, datetime.now().isoformat(timespec="seconds"))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Entry:
        return cls(
            id=int(data["id"]),
            name=str(data["name"]),
            message=str(data["message"]),
            created_at=str(data.get("created_at", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def created_display(self) -> str:
        """Thời gian dạng dd/mm/yyyy HH:MM để hiển thị."""
        try:
            return datetime.fromisoformat(self.created_at).strftime("%d/%m/%Y %H:%M")
        except ValueError:
            return self.created_at
