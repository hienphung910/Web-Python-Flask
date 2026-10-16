"""Guestbook - ứng dụng sổ lưu bút viết bằng Flask (application factory)."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from flask import Flask

from .routes import bp
from .storage import STORAGE_KEY, JsonStorage


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    """Tạo và cấu hình một Flask app mới."""
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("GUESTBOOK_SECRET_KEY", "dev-only-secret"),
        DATA_FILE=Path(app.instance_path) / "data.json",
        CHART_FILE=Path(app.static_folder) / "stats.png",
        MAX_NAME_LENGTH=50,
        MAX_MESSAGE_LENGTH=500,
        TOP_SENDERS=5,
    )
    if test_config:
        app.config.update(test_config)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    app.extensions[STORAGE_KEY] = JsonStorage(Path(app.config["DATA_FILE"]))
    app.register_blueprint(bp)
    return app
