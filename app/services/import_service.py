from __future__ import annotations

import json
import time

from app.infrastructure.steam_client import SteamClient
from app.repositories.config_repository import ConfigRepository
from app.repositories.item_repository import ItemRepository


INVENTORY_CACHE_TTL_SECONDS = 15 * 60
STEAM_RATE_LIMIT_COOLDOWN_SECONDS = 15 * 60
STEAM_REQUEST_LOCK_LEASE_SECONDS = 5 * 60


class ImportService:
    """Steam-Inventar-Import als Abgleich: Checkbox an = tracken, aus = deaktivieren.

    Die Import-Seite ist gleichzeitig die spaetere Konfigurationsoberflaeche —
    erneutes Laden des Inventars zeigt den aktuellen Tracking-Status jedes Items
    und erlaubt An-/Abwahl.
    """

    def __init__(self, repo: ItemRepository, steam: SteamClient, config_repo: ConfigRepository) -> None:
        self.repo = repo
        self.steam = steam
        self.config_repo = config_repo

    def get_saved_steam_input(self) -> str:
        return self.config_repo.get_value("steam_inventory_input", "") or ""

    @staticmethod
    def _cache_key(steam_input: str) -> str:
        return (steam_input or "").strip().casefold()

    def _build_preview_from_items(self, steam_id: str, inv_items: list[dict]) -> tuple[dict, None]:
        existing = self.repo.get_items_by_market_hash()
        preview = []
        for item in inv_items:
            db_item = existing.get(item["market_hash"])
            preview.append(
                {
                    **item,
                    "tracked": db_item is not None,
                    "active": bool(int(db_item["is_active"])) if db_item else False,
                    "db_qty": int(db_item["quantity"]) if db_item else None,
                    "item_id": int(db_item["id"]) if db_item else None,
                }
            )
        return {"steam_id": steam_id, "items": preview}, None

    def _load_cached_inventory(self, steam_input: str, now_ts: int) -> tuple[str, list[dict]] | None:
        raw = self.config_repo.get_value("steam_inventory_preview_cache_json", "")
        if not raw:
            return None
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None
        if payload.get("input_key") != self._cache_key(steam_input):
            return None
        try:
            fetched_ts = int(payload.get("fetched_ts") or 0)
        except (TypeError, ValueError):
            return None
        if now_ts - fetched_ts > INVENTORY_CACHE_TTL_SECONDS:
            return None
        steam_id = str(payload.get("steam_id") or "")
        items = payload.get("items")
        if not steam_id or not isinstance(items, list):
            return None
        return steam_id, items

    def _save_inventory_cache(self, steam_input: str, steam_id: str, inv_items: list[dict], now_ts: int) -> None:
        payload = {
            "input_key": self._cache_key(steam_input),
            "steam_id": steam_id,
            "fetched_ts": int(now_ts),
            "items": inv_items,
        }
        self.config_repo.set_value("steam_inventory_preview_cache_json", json.dumps(payload, separators=(",", ":")))

    @staticmethod
    def _format_wait_message(remaining_seconds: int) -> str:
        minutes = max(1, int((remaining_seconds + 59) / 60))
        return f"Steam-Rate-Limit aktiv. Bitte in ca. {minutes} Minuten erneut versuchen."

    def build_preview(self, steam_input: str) -> tuple[dict | None, str | None]:
        now_ts = int(time.time())
        cached = self._load_cached_inventory(steam_input, now_ts)
        if cached is not None:
            steam_id, inv_items = cached
            return self._build_preview_from_items(steam_id, inv_items)

        remaining = self.config_repo.get_steam_rate_limit_remaining_seconds(now_ts)
        if remaining > 0:
            return None, self._format_wait_message(remaining)

        if not self.config_repo.acquire_steam_request_lock(now_ts, STEAM_REQUEST_LOCK_LEASE_SECONDS):
            return None, "Steam-Abgleich laeuft bereits. Bitte gleich erneut versuchen."

        try:
            steam_id = self.steam.resolve_steam_id(steam_input)
            if not steam_id:
                return None, "SteamID nicht erkannt. Bitte SteamID64, Profil-URL oder Vanity-Namen angeben."

            inv_items, err = self.steam.fetch_inventory(steam_id)
            if err:
                if self.steam.was_rate_limited:
                    self.config_repo.mark_steam_rate_limited(now_ts, STEAM_RATE_LIMIT_COOLDOWN_SECONDS)
                return None, err

            self.config_repo.set_value("steam_inventory_input", steam_input.strip())
            self._save_inventory_cache(steam_input, steam_id, inv_items, now_ts)
            return self._build_preview_from_items(steam_id, inv_items)
        finally:
            self.config_repo.release_steam_request_lock(now_ts=int(time.time()))

    def apply_selection(self, rows: list[dict]) -> dict:
        """rows: [{market_hash, name, icon, category, qty, selected}] aus dem Preview-Formular.

        - selected & unbekannt   -> Item anlegen (inventory, Kaufpreis offen)
        - selected & deaktiviert -> reaktivieren
        - abgewaehlt & aktiv     -> deaktivieren (kein Loeschen, Historie bleibt)
        Stueckzahl wird bei getrackten Items auf den Inventar-Stand aktualisiert.
        """
        existing = self.repo.get_items_by_market_hash()
        added = reactivated = deactivated = qty_updated = 0

        for row in rows:
            mh = (row.get("market_hash") or "").strip()
            if not mh:
                continue
            selected = bool(row.get("selected"))
            qty = max(1, int(row.get("qty") or 1))
            db_item = existing.get(mh)

            if db_item is None:
                if not selected:
                    continue
                self.repo.insert_item(
                    display_name=(row.get("name") or mh).strip(),
                    market_hash=mh,
                    buy_price_cents=None,
                    icon_url=(row.get("icon") or None),
                    category=(row.get("category") or None),
                    item_type="inventory",
                    quantity=qty,
                )
                added += 1
                continue

            item_id = int(db_item["id"])
            is_active = bool(int(db_item["is_active"]))
            if selected and not is_active:
                self.repo.set_item_active(item_id, True)
                reactivated += 1
            elif not selected and is_active:
                self.repo.set_item_active(item_id, False)
                deactivated += 1

            if selected and int(db_item["quantity"]) != qty:
                self.repo.set_item_quantity(item_id, qty)
                qty_updated += 1

        if added or reactivated:
            # Scheduler-Lauf sofort faellig machen: Preise der neuen Items
            # werden im Hintergrund geladen (mit Rate-Limit-Delay).
            self.config_repo.set_value("auto_refresh_last_run_ts", "0")

        return {
            "added": added,
            "reactivated": reactivated,
            "deactivated": deactivated,
            "qty_updated": qty_updated,
        }
