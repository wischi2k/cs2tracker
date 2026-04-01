from __future__ import annotations

import time

from flask import jsonify

from app.services.setup_service import SetupService


def register_health_routes(app, setup_service: SetupService) -> None:
    @app.get("/health")
    def health() -> tuple[dict[str, object], int]:
        auto_refresh = setup_service.get_auto_refresh_status()
        summary = setup_service.get_summary_status()
        payload = {
            "ok": True,
            "setup_completed": setup_service.is_setup_completed(),
            "db_path": app.config["DATABASE_PATH"],
            "auto_refresh": auto_refresh,
            "summary": summary,
            "ts": int(time.time()),
        }
        return jsonify(payload), 200
