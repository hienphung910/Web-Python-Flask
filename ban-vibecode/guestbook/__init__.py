"""Guestbook - ứng dụng sổ lưu bút viết bằng Flask (application factory)."""

from __future__ import annotations

import os
from typing import Any

from flask import Flask

from . import storage
from .routes import bp


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    """Tạo và cấu hình một Flask app mới."""
    app = Flask(__name__)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("GUESTBOOK_SECRET_KEY", "dev-only-secret"),
        # File SQLite nằm trong thư mục instance/ (không đưa lên git)
        DATABASE=os.path.join(app.instance_path, "guestbook.db"),
        # Bản sao JSON của lời nhắn, ghi lại sau mỗi lần thêm/xóa
        DATA_FILE=os.path.join(app.instance_path, "data.json"),
        # Thư mục chứa ảnh biểu đồ của trang /stats
        CHART_DIR=app.static_folder,
        MAX_NAME_LENGTH=50,
        MAX_MESSAGE_LENGTH=500,
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(os.path.dirname(app.config["DATABASE"]), exist_ok=True)
    storage.init_app(app)
    app.register_blueprint(bp)
    return app
