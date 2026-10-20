"""Guestbook - ứng dụng sổ lưu bút viết bằng Flask (application factory)."""

from __future__ import annotations

import os
from typing import Any

from flask import Flask

from .routes import bp


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    """Tạo và cấu hình một Flask app mới."""
    app = Flask(__name__)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("GUESTBOOK_SECRET_KEY", "dev-only-secret"),
        MAX_NAME_LENGTH=50,
        MAX_MESSAGE_LENGTH=500,
    )
    if test_config:
        app.config.update(test_config)

    app.register_blueprint(bp)
    return app
