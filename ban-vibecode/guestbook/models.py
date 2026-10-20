"""Mô hình dữ liệu của một lời nhắn."""

from __future__ import annotations

import zlib
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Entry:
    id: int
    name: str
    message: str
    created_at: datetime = field(default_factory=lambda: datetime.now().replace(microsecond=0))

    @property
    def initials(self) -> str:
        """Chữ cái đầu để làm avatar: "Nguyễn Văn An" -> "NA", "An" -> "A"."""
        words = self.name.split()
        if len(words) >= 2:
            return (words[0][0] + words[-1][0]).upper()
        return self.name[:1].upper()

    @property
    def hue(self) -> int:
        """Màu avatar (0-359) suy ra từ tên, cùng tên luôn cùng màu.

        Dùng crc32 thay vì hash() vì hash() của Python đổi giá trị mỗi lần chạy lại.
        """
        return zlib.crc32(self.name.casefold().encode("utf-8")) % 360

    @property
    def created_iso(self) -> str:
        return self.created_at.isoformat(timespec="seconds")

    @property
    def created_display(self) -> str:
        """Thời gian dạng dd/mm/yyyy HH:MM."""
        return self.created_at.strftime("%d/%m/%Y %H:%M")

    def created_relative(self, now: datetime | None = None) -> str:
        """Thời gian tương đối: "vừa xong", "5 phút trước", ..."""
        seconds = int(((now or datetime.now()) - self.created_at).total_seconds())
        if seconds < 60:
            return "vừa xong"
        if seconds < 3600:
            return f"{seconds // 60} phút trước"
        if seconds < 86400:
            return f"{seconds // 3600} giờ trước"
        if seconds < 7 * 86400:
            return f"{seconds // 86400} ngày trước"
        return self.created_display
