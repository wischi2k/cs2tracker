from __future__ import annotations

import ipaddress
import os
import re
from flask import Request

from app.repositories.config_repository import ConfigRepository


VALID_THEMES = {"dark", "highlighter-noir", "safety-lime", "cleanroom-lime"}


class SetupService:
    def __init__(self, config_repo: ConfigRepository) -> None:
        self.config_repo = config_repo

    def ensure_default_config(self) -> None:
        self.config_repo.set_default_value("ui_theme", "dark")
        self.config_repo.set_default_value("setup_completed", "false")
        self.config_repo.set_default_value("price_update_interval_minutes", "30")
        self.config_repo.set_default_value("notifications_enabled", "false")
        self.config_repo.set_default_value("ui_access_scope", "private_network")
        self.config_repo.set_default_value("auto_refresh_last_run_ts", "0")
        self.config_repo.set_default_value("auto_refresh_last_status", "never")
        self.config_repo.set_default_value("auto_refresh_last_error", "")
        self.config_repo.set_default_value("auto_refresh_last_updated_items", "0")
        self.config_repo.set_default_value("auto_refresh_lock_until_ts", "0")
        self.config_repo.set_default_value("steam_request_lock_until_ts", "0")
        self.config_repo.set_default_value("steam_rate_limit_until_ts", "0")
        self.config_repo.set_default_value("summary_enabled", "false")
        self.config_repo.set_default_value("summary_interval_days", "7")
        self.config_repo.set_default_value("summary_send_time", "09:00")
        self.config_repo.set_default_value("summary_last_sent_ts", "0")
        self.config_repo.set_default_value("summary_last_status", "never")
        self.config_repo.set_default_value("summary_last_error", "")
        self.config_repo.set_default_value("summary_last_sent_items", "0")
        self.config_repo.set_default_value("summary_lock_until_ts", "0")

    def get_ui_theme(self) -> str:
        raw = (self.config_repo.get_value("ui_theme", "dark") or "").strip().lower()
        return raw if raw in VALID_THEMES else "dark"

    def is_setup_completed(self) -> bool:
        raw = (self.config_repo.get_value("setup_completed", "false") or "").strip().lower()
        return raw in {"1", "true", "yes", "on"}

    def get_bool(self, key: str, default: bool = False) -> bool:
        raw = self.config_repo.get_value(key, "true" if default else "false") or ""
        return raw.strip().lower() in {"1", "true", "yes", "on"}

    def get_interval(self) -> str:
        return self.config_repo.get_value("price_update_interval_minutes", "30") or "30"

    def get_summary_enabled(self) -> bool:
        return self.get_bool("summary_enabled", default=False)

    def get_summary_interval_days(self) -> str:
        raw = self.config_repo.get_value("summary_interval_days", "7") or "7"
        try:
            days = int(raw.strip())
        except ValueError:
            days = 7
        days = max(1, min(days, 365))
        return str(days)

    def get_summary_send_time(self) -> str:
        raw = (self.config_repo.get_value("summary_send_time", "09:00") or "09:00").strip()
        if not self._is_valid_hhmm(raw):
            return "09:00"
        return raw

    def get_ui_access_scope(self) -> str:
        raw = (self.config_repo.get_value("ui_access_scope", "private_network") or "").strip().lower()
        if raw not in {"local_only", "private_network"}:
            return "private_network"
        return raw

    @staticmethod
    def _is_valid_hhmm(raw: str) -> bool:
        if not re.match(r"^\d{2}:\d{2}$", raw):
            return False
        hh, mm = raw.split(":")
        h = int(hh)
        m = int(mm)
        return 0 <= h <= 23 and 0 <= m <= 59

    def set_general_config(
        self,
        interval_raw: str,
        notifications_enabled: bool,
        ui_access_scope: str,
        summary_enabled: bool,
        summary_interval_days_raw: str,
        summary_send_time_raw: str,
        ui_theme: str = "dark",
    ) -> int:
        try:
            interval = int((interval_raw or "").strip())
        except ValueError:
            interval = 30
        interval = max(5, min(interval, 1440))
        self.config_repo.set_value("price_update_interval_minutes", str(interval))
        self.config_repo.set_value("notifications_enabled", "true" if notifications_enabled else "false")
        scope = (ui_access_scope or "").strip().lower()
        if scope not in {"local_only", "private_network"}:
            scope = "private_network"
        self.config_repo.set_value("ui_access_scope", scope)

        self.config_repo.set_value("summary_enabled", "true" if summary_enabled else "false")
        try:
            summary_days = int((summary_interval_days_raw or "").strip())
        except ValueError:
            summary_days = 7
        summary_days = max(1, min(summary_days, 365))
        self.config_repo.set_value("summary_interval_days", str(summary_days))

        send_time = (summary_send_time_raw or "").strip()
        if not self._is_valid_hhmm(send_time):
            send_time = "09:00"
        self.config_repo.set_value("summary_send_time", send_time)

        theme = (ui_theme or "").strip().lower()
        if theme not in VALID_THEMES:
            theme = "dark"
        self.config_repo.set_value("ui_theme", theme)

        return interval

    def complete_setup(self) -> None:
        self.config_repo.set_value("setup_completed", "true")

    def save_telegram_credentials(self, token: str, chat_id: str) -> None:
        self.config_repo.set_secret("telegram_bot_token", token)
        self.config_repo.set_secret("telegram_chat_id", chat_id)
        self.config_repo.set_value("notifications_enabled", "true")

    def get_telegram_credentials(self) -> tuple[str | None, str | None]:
        token = self.config_repo.get_secret("telegram_bot_token") or os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = self.config_repo.get_secret("telegram_chat_id") or os.getenv("TELEGRAM_CHAT_ID")
        return token, chat_id

    def has_telegram_credentials(self) -> bool:
        token, chat_id = self.get_telegram_credentials()
        return bool(token and chat_id)

    def get_auto_refresh_status(self) -> dict[str, int | str | None]:
        return self.config_repo.get_auto_refresh_status()

    def get_summary_status(self) -> dict[str, int | str | bool | None]:
        return self.config_repo.get_summary_status()

    @staticmethod
    def _client_ip(request: Request):
        addr = (request.headers.get("X-Forwarded-For", request.remote_addr) or "").split(",")[0].strip()
        if not addr:
            return None
        try:
            return ipaddress.ip_address(addr)
        except ValueError:
            return None

    def client_is_local_or_private(self, request: Request) -> bool:
        ip = self._client_ip(request)
        if ip is None:
            return False
        return ip.is_loopback or ip.is_private

    def client_is_allowed_for_scope(self, request: Request, scope: str) -> bool:
        ip = self._client_ip(request)
        if ip is None:
            return False
        if scope == "local_only":
            return ip.is_loopback
        return ip.is_loopback or ip.is_private
