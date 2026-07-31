from __future__ import annotations

import threading
import time

from flask import Flask

from app.infrastructure.telegram_client import TelegramClient
from app.repositories.config_repository import ConfigRepository
from app.services.item_service import ItemService
from app.services.setup_service import SetupService
from app.services.summary_service import SummaryService


class PriceSchedulerService:
    def __init__(
        self,
        config_repo: ConfigRepository,
        item_service: ItemService,
        summary_service: SummaryService,
        telegram: TelegramClient,
        setup_service: SetupService,
        app: Flask,
        poll_seconds: int = 15,
        lock_lease_seconds: int = 600,
    ) -> None:
        self.config_repo = config_repo
        self.item_service = item_service
        self.summary_service = summary_service
        self.telegram = telegram
        self.setup_service = setup_service
        self.app = app
        self.poll_seconds = max(5, int(poll_seconds))
        self.lock_lease_seconds = max(60, int(lock_lease_seconds))
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="price-scheduler")
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _read_interval_seconds(self) -> int:
        raw = self.config_repo.get_value("price_update_interval_minutes", "30") or "30"
        try:
            minutes = int(raw.strip())
        except ValueError:
            minutes = 30
        minutes = max(5, min(minutes, 1440))
        return minutes * 60

    def _is_due(self, now_ts: int, interval_seconds: int) -> bool:
        raw_last = self.config_repo.get_value("auto_refresh_last_run_ts", "0") or "0"
        try:
            last_run_ts = int(raw_last.strip())
        except ValueError:
            last_run_ts = 0
        return (now_ts - last_run_ts) >= interval_seconds

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            with self.app.app_context():
                self.run_due_once()
                self.run_summary_due_once()
            self._stop_event.wait(self.poll_seconds)

    def run_due_once(self) -> None:
        now_ts = int(time.time())
        interval_seconds = self._read_interval_seconds()
        if not self._is_due(now_ts, interval_seconds):
            return

        if not self.config_repo.acquire_auto_refresh_lock(now_ts=now_ts, lease_seconds=self.lock_lease_seconds):
            return

        try:
            updated_count, _skipped_count = self.item_service.refresh_all_active_prices()
            self.item_service.check_and_fire_alerts()
            self.summary_service.record_portfolio_snapshot()
            finished_ts = int(time.time())
            self.config_repo.set_value("auto_refresh_last_run_ts", str(finished_ts))
            self.config_repo.set_value("auto_refresh_last_status", "ok")
            self.config_repo.set_value("auto_refresh_last_error", "")
            self.config_repo.set_value("auto_refresh_last_updated_items", str(updated_count))
        except Exception as exc:
            finished_ts = int(time.time())
            self.config_repo.set_value("auto_refresh_last_run_ts", str(finished_ts))
            self.config_repo.set_value("auto_refresh_last_status", "error")
            self.config_repo.set_value("auto_refresh_last_error", str(exc)[:300])
        finally:
            self.config_repo.release_auto_refresh_lock(now_ts=int(time.time()))

    @staticmethod
    def _parse_hhmm(send_time_raw: str) -> tuple[int, int] | None:
        raw = (send_time_raw or "").strip()
        if len(raw) != 5 or raw[2] != ":":
            return None
        try:
            hh = int(raw[:2])
            mm = int(raw[3:])
        except ValueError:
            return None
        if not (0 <= hh <= 23 and 0 <= mm <= 59):
            return None
        return hh, mm

    def run_summary_due_once(self) -> None:
        status = self.setup_service.get_summary_status()
        if not bool(status.get("enabled")):
            return

        token, chat_id = self.setup_service.get_telegram_credentials()
        if not token or not chat_id:
            return

        now_ts = int(time.time())
        interval_days = int(status.get("interval_days") or 7)
        interval_days = max(1, min(interval_days, 365))
        interval_seconds = interval_days * 86400
        last_sent_ts = int(status.get("last_sent_ts") or 0)
        if (now_ts - last_sent_ts) < interval_seconds:
            return

        parsed = self._parse_hhmm(str(status.get("send_time") or "09:00"))
        if parsed is None:
            parsed = (9, 0)
        send_hh, send_mm = parsed
        lt = time.localtime(now_ts)
        if (lt.tm_hour, lt.tm_min) < (send_hh, send_mm):
            return

        if not self.config_repo.acquire_summary_lock(now_ts=now_ts, lease_seconds=self.lock_lease_seconds):
            return

        try:
            self._send_summary(interval_days=interval_days, token=token, chat_id=chat_id)
        except Exception as exc:
            self.config_repo.set_value("summary_last_status", "error")
            self.config_repo.set_value("summary_last_error", str(exc)[:300])
        finally:
            self.config_repo.release_summary_lock(now_ts=int(time.time()))

    def _send_summary(self, interval_days: int, token: str, chat_id: str) -> tuple[bool, str]:
        payload = self.summary_service.build_summary(interval_days=interval_days)
        ok = self.telegram.send(payload.text_html, token=token, chat_id=chat_id)
        finished_ts = int(time.time())
        if not ok:
            self.config_repo.set_value("summary_last_status", "error")
            self.config_repo.set_value("summary_last_error", "Telegram send failed for summary")
            return False, "Telegram-Versand fehlgeschlagen."

        self.config_repo.set_value("summary_last_sent_ts", str(finished_ts))
        self.config_repo.set_value("summary_last_status", "ok")
        self.config_repo.set_value("summary_last_error", "")
        self.config_repo.set_value("summary_last_sent_items", str(payload.considered_items))
        return True, "Summary wurde gesendet."

    def run_summary_now_once(self) -> tuple[bool, str]:
        status = self.setup_service.get_summary_status()
        if not bool(status.get("enabled")):
            return False, "Telegram-Zusammenfassung ist deaktiviert."

        token, chat_id = self.setup_service.get_telegram_credentials()
        if not token or not chat_id:
            return False, "Telegram ist nicht konfiguriert."

        interval_days = int(status.get("interval_days") or 7)
        interval_days = max(1, min(interval_days, 365))
        now_ts = int(time.time())

        if not self.config_repo.acquire_summary_lock(now_ts=now_ts, lease_seconds=self.lock_lease_seconds):
            return False, "Summary ist gerade gesperrt (laufender Job). Bitte gleich erneut versuchen."

        try:
            return self._send_summary(interval_days=interval_days, token=token, chat_id=chat_id)
        except Exception as exc:
            self.config_repo.set_value("summary_last_status", "error")
            self.config_repo.set_value("summary_last_error", str(exc)[:300])
            return False, f"Summary-Fehler: {str(exc)[:200]}"
        finally:
            self.config_repo.release_summary_lock(now_ts=int(time.time()))
