from __future__ import annotations

import time

from flask import abort, flash, redirect, render_template, request, url_for

from app.infrastructure.telegram_client import TelegramClient
from app.services.setup_service import SetupService


def register_setup_routes(app, setup_service: SetupService, telegram: TelegramClient) -> None:
    def _fmt_ts(ts: int | None) -> str:
        if not ts:
            return "-"
        try:
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(ts)))
        except Exception:
            return "-"

    @app.context_processor
    def inject_global_template_state():
        return {
            "setup_completed_global": setup_service.is_setup_completed(),
            "ui_theme": setup_service.get_ui_theme(),
        }

    @app.before_request
    def enforce_setup_and_admin_access():
        endpoint = request.endpoint or ""
        if not endpoint:
            return None
        if endpoint == "static":
            return None

        scope = setup_service.get_ui_access_scope()
        if endpoint != "health" and not setup_service.client_is_allowed_for_scope(request, scope):
            abort(403, description="Access denied by configured UI access scope.")

        protected = {
            "setup",
            "setup_general",
            "setup_telegram",
            "setup_complete",
            "settings",
            "settings_general",
            "settings_telegram",
            "settings_summary_send_now",
            "import_inventory",
            "import_preview",
            "import_apply",
        }
        if endpoint in protected and not setup_service.client_is_local_or_private(request):
            abort(403, description="Setup/Settings are only available from local or private network addresses.")

        exempt_when_unconfigured = {
            "setup",
            "setup_general",
            "setup_telegram",
            "setup_complete",
            "health",
        }
        if not setup_service.is_setup_completed() and endpoint not in exempt_when_unconfigured:
            return redirect(url_for("setup"))
        return None

    @app.get("/setup")
    def setup():
        return render_template(
            "setup.html",
            setup_completed=setup_service.is_setup_completed(),
            interval=setup_service.get_interval(),
            notifications_enabled=setup_service.get_bool("notifications_enabled", default=False),
            ui_access_scope=setup_service.get_ui_access_scope(),
            summary_enabled=setup_service.get_summary_enabled(),
            summary_interval_days=setup_service.get_summary_interval_days(),
            summary_send_time=setup_service.get_summary_send_time(),
            telegram_configured=setup_service.has_telegram_credentials(),
            ui_theme=setup_service.get_ui_theme(),
        )

    @app.post("/setup/general")
    def setup_general():
        setup_service.set_general_config(
            interval_raw=(request.form.get("price_update_interval_minutes") or "30"),
            notifications_enabled=(request.form.get("notifications_enabled") == "on"),
            ui_access_scope=(request.form.get("ui_access_scope") or "private_network"),
            summary_enabled=(request.form.get("summary_enabled") == "on"),
            summary_interval_days_raw=(request.form.get("summary_interval_days") or "7"),
            summary_send_time_raw=(request.form.get("summary_send_time") or "09:00"),
            ui_theme=(request.form.get("ui_theme") or "dark"),
        )
        flash("Grundkonfiguration gespeichert.", "success")
        return redirect(url_for("setup"))

    @app.post("/settings/general")
    def settings_general():
        setup_service.set_general_config(
            interval_raw=(request.form.get("price_update_interval_minutes") or "30"),
            notifications_enabled=(request.form.get("notifications_enabled") == "on"),
            ui_access_scope=(request.form.get("ui_access_scope") or "private_network"),
            summary_enabled=(request.form.get("summary_enabled") == "on"),
            summary_interval_days_raw=(request.form.get("summary_interval_days") or "7"),
            summary_send_time_raw=(request.form.get("summary_send_time") or "09:00"),
            ui_theme=(request.form.get("ui_theme") or "dark"),
        )
        flash("Einstellungen gespeichert.", "success")
        return redirect(url_for("settings"))

    @app.post("/setup/telegram")
    def setup_telegram():
        token = (request.form.get("bot_token") or "").strip()
        chat_id = (request.form.get("chat_id") or "").strip()
        if not token or not chat_id:
            flash("Bitte Bot-Token und Chat-ID eingeben.", "error")
            return redirect(url_for("setup"))

        ok = telegram.send(
            "CS2 Tracker Setup-Test: Telegram ist verbunden.",
            token=token,
            chat_id=chat_id,
        )
        if not ok:
            flash("Telegram-Test fehlgeschlagen. Bitte Token/Chat-ID pruefen.", "error")
            return redirect(url_for("setup"))

        setup_service.save_telegram_credentials(token, chat_id)
        flash("Telegram erfolgreich verbunden und gespeichert.", "success")
        return redirect(url_for("setup"))

    @app.post("/setup/complete")
    def setup_complete():
        setup_service.complete_setup()
        flash("Setup abgeschlossen.", "success")
        return redirect(url_for("index"))

    @app.get("/settings")
    def settings():
        summary_status = setup_service.get_summary_status()
        last_sent_ts = int(summary_status.get("last_sent_ts") or 0)
        lock_until_ts = int(summary_status.get("lock_until_ts") or 0)
        return render_template(
            "settings.html",
            interval=setup_service.get_interval(),
            notifications_enabled=setup_service.get_bool("notifications_enabled", default=False),
            ui_access_scope=setup_service.get_ui_access_scope(),
            summary_enabled=setup_service.get_summary_enabled(),
            summary_interval_days=setup_service.get_summary_interval_days(),
            summary_send_time=setup_service.get_summary_send_time(),
            summary_status=summary_status,
            summary_last_sent_human=_fmt_ts(last_sent_ts),
            summary_lock_until_human=_fmt_ts(lock_until_ts),
            telegram_configured=setup_service.has_telegram_credentials(),
            now_ts=int(time.time()),
            ui_theme=setup_service.get_ui_theme(),
        )

    @app.post("/settings/telegram")
    def settings_telegram():
        token = (request.form.get("bot_token") or "").strip()
        chat_id = (request.form.get("chat_id") or "").strip()
        if not token or not chat_id:
            flash("Bitte Bot-Token und Chat-ID eingeben.", "error")
            return redirect(url_for("settings"))

        ok = telegram.send(
            "CS2 Tracker Einstellungen-Test: Telegram ist verbunden.",
            token=token,
            chat_id=chat_id,
        )
        if not ok:
            flash("Telegram-Test fehlgeschlagen. Bitte Token/Chat-ID pruefen.", "error")
            return redirect(url_for("settings"))

        setup_service.save_telegram_credentials(token, chat_id)
        flash("Telegram-Einstellungen gespeichert.", "success")
        return redirect(url_for("settings"))

    @app.post("/settings/summary/send-now")
    def settings_summary_send_now():
        scheduler = app.extensions.get("price_scheduler")
        if scheduler is None:
            flash("Summary-Scheduler ist nicht verfuegbar.", "error")
            return redirect(url_for("settings"))

        ok, msg = scheduler.run_summary_now_once()
        flash(msg, "success" if ok else "error")
        return redirect(url_for("settings"))
