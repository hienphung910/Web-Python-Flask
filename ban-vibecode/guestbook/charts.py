"""Vẽ biểu đồ số lời nhắn theo người gửi bằng Matplotlib.

Dùng `matplotlib.figure.Figure` trực tiếp thay vì `pyplot`: không cần chọn backend,
không có trạng thái toàn cục nên an toàn khi nhiều request vẽ cùng lúc.

Mỗi lần vẽ tạo hai ảnh nền trong suốt, một cho giao diện sáng và một cho giao diện tối;
CSS chọn ảnh hợp với theme đang dùng.
"""

from __future__ import annotations

from pathlib import Path

from matplotlib.figure import Figure

# Màu cột chính trùng màu điểm nhấn của trang; cột "Khác" màu xám trung tính.
# Đã kiểm tra tương phản >= 3:1 với nền thẻ ở cả hai chế độ.
THEMES = {
    "light": {"bar": "#e4572e", "other": "#8a847e", "text": "#1c1917", "muted": "#78716c"},
    "dark": {"bar": "#e9603a", "other": "#7c766f", "text": "#f5f5f4", "muted": "#a8a29e"},
}

MAX_BARS = 10


def fold_tail(counts: list[tuple[str, int]], limit: int = MAX_BARS) -> list[tuple[str, int]]:
    """Giữ tối đa `limit` cột: quá thì gộp phần đuôi thành một cột "Khác"."""
    if len(counts) <= limit:
        return counts
    head, tail = counts[: limit - 1], counts[limit - 1 :]
    return [*head, (f"Khác ({len(tail)} người)", sum(n for _, n in tail))]


def render_sender_chart(counts: list[tuple[str, int]], out_dir: Path) -> None:
    """Vẽ biểu đồ cột ngang và lưu thành stats.png (sáng) + stats-dark.png (tối)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = fold_tail(counts)
    folded = len(rows) < len(counts)
    for theme, filename in (("light", "stats.png"), ("dark", "stats-dark.png")):
        fig = _draw(rows, folded, THEMES[theme])
        fig.savefig(out_dir / filename, dpi=150, transparent=True)


def _draw(rows: list[tuple[str, int]], folded: bool, colors: dict[str, str]) -> Figure:
    names = [name for name, _ in rows]
    values = [n for _, n in rows]
    bar_colors = [colors["bar"]] * len(rows)
    if folded:
        bar_colors[-1] = colors["other"]

    fig = Figure(figsize=(6, 0.5 + 0.42 * len(rows)), layout="constrained")
    ax = fig.add_subplot()

    # Người gửi nhiều nhất nằm trên cùng
    y = range(len(rows))
    ax.barh(y, values, height=0.56, color=bar_colors)
    ax.invert_yaxis()
    ax.set_yticks(list(y), names)

    # Mỗi cột đã có số ở đầu cột nên bỏ trục x, khung và lưới cho gọn
    for value, pos in zip(values, y):
        ax.annotate(
            str(value), (value, pos), xytext=(6, 0), textcoords="offset points",
            va="center", color=colors["text"], fontsize=11, fontweight="bold",
        )
    ax.set_xlim(0, max(values) * 1.12)
    ax.xaxis.set_visible(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(axis="y", length=0, pad=8, labelcolor=colors["muted"], labelsize=11)
    return fig
