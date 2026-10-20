"""Guestbook - ứng dụng sổ lưu bút viết bằng Flask (application factory)."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from flask import Flask

from .routes import bp
from .storage import STORAGE_KEY, SqliteStorage


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    """Tạo và cấu hình một Flask app mới."""
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("GUESTBOOK_SECRET_KEY", "dev-only-secret"),
        # File SQLite nằm trong thư mục instance/ (git ignore), tự tạo khi chạy lần đầu
        DB_FILE=Path(app.instance_path) / "guestbook.db",
        CHART_FILE=Path(app.static_folder) / "stats.png",
        MAX_NAME_LENGTH=50,
        MAX_MESSAGE_LENGTH=500,
        TOP_SENDERS=5,
    )
    app.config.from_pyfile("config.py", silent=True)
    if test_config:
        app.config.update(test_config)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    app.extensions[STORAGE_KEY] = SqliteStorage(app.config["DB_FILE"])
    app.register_blueprint(bp)
    return app
