"""Thống kê và vẽ biểu đồ."""

from __future__ import annotations

import io
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

from .models import Entry
from .storage import atomic_write

BAR_COLOR = "#4f46e5"
TEXT_COLOR = "#334155"


def count_by_sender(entries: Iterable[Entry]) -> Counter[str]:
    return Counter(entry.name for entry in entries)


def render_bar_chart(counts: Counter[str], output: Path) -> bool:
    """Vẽ biểu đồ cột số lời nhắn theo người gửi, lưu ra file PNG.

    Dùng trực tiếp Figure (không qua pyplot) nên an toàn khi chạy trong web server
    nhiều thread, và không cần matplotlib.use("Agg").
    Trả về False nếu không có dữ liệu để vẽ.
    """
    if not counts:
        return False

    names, values = zip(*counts.most_common())

    fig = Figure(figsize=(max(6.0, 0.9 * len(names)), 4), dpi=110)
    ax = fig.subplots()
    bars = ax.bar(names, values, color=BAR_COLOR, width=0.6)
    ax.bar_label(bars, padding=3, color=TEXT_COLOR)

    ax.set_title("Số lời nhắn theo người gửi", color=TEXT_COLOR, fontsize=13, pad=12)
    ax.set_ylabel("Số lời nhắn", color=TEXT_COLOR)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_ylim(0, max(values) * 1.15)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.3)
    ax.set_axisbelow(True)
    ax.tick_params(colors=TEXT_COLOR)
    if len(names) > 5:
        ax.tick_params(axis="x", labelrotation=30)
    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png")
    atomic_write(output, buffer.getvalue())
    return True
