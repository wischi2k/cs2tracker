from __future__ import annotations

import os

import requests

from app.repositories.config_repository import ConfigRepository


class TelegramClient:
    def __init__(self, config_repo: ConfigRepository | None = None) -> None:
        self._config_repo = config_repo

    def _resolve_credentials(self, token: str | None, chat_id: str | None) -> tuple[str | None, str | None]:
        if token and chat_id:
            return token, chat_id

        token_db = None
        chat_db = None
        if self._config_repo is not None:
            token_db = self._config_repo.get_secret("telegram_bot_token")
            chat_db = self._config_repo.get_secret("telegram_chat_id")

        return (
            token or token_db or os.getenv("TELEGRAM_BOT_TOKEN"),
            chat_id or chat_db or os.getenv("TELEGRAM_CHAT_ID"),
        )

    def send(self, text: str, token: str | None = None, chat_id: str | None = None) -> bool:
        resolved_token, resolved_chat = self._resolve_credentials(token, chat_id)
        if not resolved_token or not resolved_chat:
            return False
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{resolved_token}/sendMessage",
                data={
                    "chat_id": resolved_chat,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": 1,
                },
                timeout=15,
            )
            return bool(r.ok)
        except Exception:
            return False
