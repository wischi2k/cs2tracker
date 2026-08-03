from __future__ import annotations

import time

from app.db import get_connection
from app.infrastructure.secret_store import decrypt_secret, encrypt_secret


class ConfigRepository:
    def ensure_schema(self) -> None:
        con = get_connection()
        try:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS app_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at INTEGER NOT NULL
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS secret_store (
                    key TEXT PRIMARY KEY,
                    ciphertext TEXT NOT NULL,
                    nonce TEXT NOT NULL,
                    updated_at INTEGER NOT NULL
                )
                """
            )
            con.commit()
        finally:
            con.close()

    def get_value(self, key: str, default: str | None = None) -> str | None:
        con = get_connection()
        try:
            row = con.execute("SELECT value FROM app_config WHERE key=?", (key,)).fetchone()
            return default if row is None else str(row[0])
        finally:
            con.close()

    def set_value(self, key: str, value: str) -> None:
        con = get_connection()
        try:
            con.execute(
                """
                INSERT INTO app_config(key, value, updated_at) VALUES(?,?,?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
                """,
                (key, value, int(time.time())),
            )
            con.commit()
        finally:
            con.close()

    def set_default_value(self, key: str, value: str) -> None:
        con = get_connection()
        try:
            con.execute(
                """
                INSERT OR IGNORE INTO app_config(key, value, updated_at) VALUES(?,?,?)
                """,
                (key, value, int(time.time())),
            )
            con.commit()
        finally:
            con.close()

    def set_secret(self, key: str, value: str) -> None:
        ciphertext, nonce = encrypt_secret(value)
        con = get_connection()
        try:
            con.execute(
                """
                INSERT INTO secret_store(key, ciphertext, nonce, updated_at) VALUES(?,?,?,?)
                ON CONFLICT(key) DO UPDATE SET
                    ciphertext=excluded.ciphertext,
                    nonce=excluded.nonce,
                    updated_at=excluded.updated_at
                """,
                (key, ciphertext, nonce, int(time.time())),
            )
            con.commit()
        finally:
            con.close()

    def get_secret(self, key: str) -> str | None:
        con = get_connection()
        try:
            row = con.execute("SELECT ciphertext, nonce FROM secret_store WHERE key=?", (key,)).fetchone()
            if row is None:
                return None
            return decrypt_secret(str(row[0]), str(row[1]))
        finally:
            con.close()

    @staticmethod
    def _to_int(value: str | None, default: int = 0) -> int:
        try:
            return int((value or "").strip())
        except (ValueError, AttributeError):
            return default

    @staticmethod
    def _to_bool(value: str | None, default: bool = False) -> bool:
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "on"}

    def acquire_auto_refresh_lock(self, now_ts: int, lease_seconds: int = 600) -> bool:
        con = get_connection()
        try:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute(
                "SELECT value FROM app_config WHERE key='auto_refresh_lock_until_ts'"
            ).fetchone()
            lock_until = self._to_int(str(row[0]) if row else None, default=0)
            if lock_until > int(now_ts):
                con.rollback()
                return False

            new_lock_until = int(now_ts) + int(lease_seconds)
            con.execute(
                """
                INSERT INTO app_config(key, value, updated_at) VALUES('auto_refresh_lock_until_ts', ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
                """,
                (str(new_lock_until), int(now_ts)),
            )
            con.commit()
            return True
        finally:
            con.close()

    def release_auto_refresh_lock(self, now_ts: int) -> None:
        self.set_value("auto_refresh_lock_until_ts", "0")
        self.set_value("auto_refresh_lock_released_ts", str(int(now_ts)))

    def acquire_steam_request_lock(self, now_ts: int, lease_seconds: int = 300) -> bool:
        con = get_connection()
        try:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute(
                "SELECT value FROM app_config WHERE key='steam_request_lock_until_ts'"
            ).fetchone()
            lock_until = self._to_int(str(row[0]) if row else None, default=0)
            if lock_until > int(now_ts):
                con.rollback()
                return False

            new_lock_until = int(now_ts) + int(lease_seconds)
            con.execute(
                """
                INSERT INTO app_config(key, value, updated_at) VALUES('steam_request_lock_until_ts', ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
                """,
                (str(new_lock_until), int(now_ts)),
            )
            con.commit()
            return True
        finally:
            con.close()

    def release_steam_request_lock(self, now_ts: int) -> None:
        self.set_value("steam_request_lock_until_ts", "0")
        self.set_value("steam_request_lock_released_ts", str(int(now_ts)))

    def get_steam_rate_limit_remaining_seconds(self, now_ts: int) -> int:
        raw = self.get_value("steam_rate_limit_until_ts", "0")
        until_ts = self._to_int(raw, default=0)
        return max(0, until_ts - int(now_ts))

    def mark_steam_rate_limited(self, now_ts: int, cooldown_seconds: int = 900) -> None:
        until_ts = int(now_ts) + max(60, int(cooldown_seconds))
        self.set_value("steam_rate_limit_until_ts", str(until_ts))

    def get_auto_refresh_status(self) -> dict[str, int | str | None]:
        return {
            "last_run_ts": self._to_int(self.get_value("auto_refresh_last_run_ts"), default=0),
            "last_status": self.get_value("auto_refresh_last_status"),
            "last_error": self.get_value("auto_refresh_last_error"),
            "last_updated_items": self._to_int(self.get_value("auto_refresh_last_updated_items"), default=0),
            "lock_until_ts": self._to_int(self.get_value("auto_refresh_lock_until_ts"), default=0),
            "steam_lock_until_ts": self._to_int(self.get_value("steam_request_lock_until_ts"), default=0),
            "steam_rate_limit_until_ts": self._to_int(self.get_value("steam_rate_limit_until_ts"), default=0),
        }

    def acquire_summary_lock(self, now_ts: int, lease_seconds: int = 600) -> bool:
        con = get_connection()
        try:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute(
                "SELECT value FROM app_config WHERE key='summary_lock_until_ts'"
            ).fetchone()
            lock_until = self._to_int(str(row[0]) if row else None, default=0)
            if lock_until > int(now_ts):
                con.rollback()
                return False

            new_lock_until = int(now_ts) + int(lease_seconds)
            con.execute(
                """
                INSERT INTO app_config(key, value, updated_at) VALUES('summary_lock_until_ts', ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
                """,
                (str(new_lock_until), int(now_ts)),
            )
            con.commit()
            return True
        finally:
            con.close()

    def release_summary_lock(self, now_ts: int) -> None:
        self.set_value("summary_lock_until_ts", "0")
        self.set_value("summary_lock_released_ts", str(int(now_ts)))

    def get_summary_status(self) -> dict[str, int | str | bool | None]:
        interval_days = self._to_int(self.get_value("summary_interval_days", "7"), default=7)
        if interval_days < 1:
            interval_days = 1
        if interval_days > 365:
            interval_days = 365

        send_time = self.get_value("summary_send_time", "09:00") or "09:00"

        return {
            "enabled": self._to_bool(self.get_value("summary_enabled", "false"), default=False),
            "interval_days": interval_days,
            "send_time": send_time,
            "last_sent_ts": self._to_int(self.get_value("summary_last_sent_ts"), default=0),
            "last_status": self.get_value("summary_last_status", "never"),
            "last_error": self.get_value("summary_last_error", ""),
            "last_sent_items": self._to_int(self.get_value("summary_last_sent_items"), default=0),
            "lock_until_ts": self._to_int(self.get_value("summary_lock_until_ts"), default=0),
        }
