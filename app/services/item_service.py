from __future__ import annotations

import html
import time
from dataclasses import asdict

from app.domain.models import ItemView
from app.infrastructure.steam_client import SteamClient
from app.infrastructure.telegram_client import TelegramClient
from app.repositories.item_repository import ItemRepository

FEE_RATE = 0.15
CATEGORIES = [
    "Waffen-Skin",
    "Sticker",
    "Agent",
    "Kiste",
    "Messer",
    "Handschuhe",
    "Schluessel",
    "Patch",
    "Musik-Kit",
    "Unbekannt",
]


class ItemService:
    def __init__(self, repo: ItemRepository, steam: SteamClient, telegram: TelegramClient | None = None) -> None:
        self.repo = repo
        self.steam = steam
        self.telegram = telegram

    @staticmethod
    def _eur(cents: int | None) -> float | None:
        return None if cents is None else cents / 100.0

    @staticmethod
    def _infer_category(raw: str) -> str:
        txt = (raw or "").lower()
        if "sticker" in txt or "aufkleber" in txt:
            return "Sticker"
        if "case" in txt or "kiste" in txt or "container" in txt:
            return "Kiste"
        if "agent" in txt:
            return "Agent"
        if "music kit" in txt or "musik-kit" in txt or "musikkit" in txt:
            return "Musik-Kit"
        if "patch" in txt:
            return "Patch"
        if "knife" in txt or "messer" in txt:
            return "Messer"
        if "gloves" in txt or "handschuhe" in txt:
            return "Handschuhe"
        if "key" in txt or "schluessel" in txt:
            return "Schluessel"
        return "Waffen-Skin"

    def _to_item_view(self, row: dict) -> ItemView:
        buy_c = row.get("buy_price_cents")
        cur_c = row.get("current_price_cents")
        net_c = None if cur_c is None else int(round(cur_c * (1 - FEE_RATE)))
        category = row.get("category")
        if not category:
            category = self._infer_category((row.get("market_hash") or row.get("display_name") or ""))
        item_type = row.get("item_type") or "inventory"
        return ItemView(
            id=int(row["id"]),
            name=row.get("display_name") or "",
            icon=row.get("icon_url"),
            icon_updated_at=int(row.get("icon_updated_at") or 0),
            cat=category,
            active=int(row.get("is_active") or 1),
            item_type=item_type,
            buy=self._eur(buy_c),
            cur=self._eur(cur_c),
            net=self._eur(net_c),
            diff_g=None if buy_c is None or cur_c is None else self._eur(cur_c - buy_c),
            diff_n=None if buy_c is None or cur_c is None else self._eur(net_c - buy_c),
            qty=max(1, int(row.get("quantity") or 1)),
        )

    def list_items(self, selected_category: str) -> tuple[list[dict], list[str]]:
        rows = self.repo.list_items_with_latest_price()
        items = [asdict(self._to_item_view(r)) for r in rows]
        all_cats = sorted({(it["cat"] or "Unbekannt") for it in items} | {"Alle"})
        if selected_category != "Alle":
            items = [it for it in items if (it["cat"] or "Unbekannt") == selected_category]
        return items, all_cats

    def get_item_view(self, item_id: int) -> dict | None:
        row = self.repo.get_item_with_latest_price(item_id)
        if row is None:
            return None
        return asdict(self._to_item_view(row))

    def get_chart_payload(self, item_id: int, buy_eur: float | None) -> dict:
        ts, cents = self.repo.get_chart_series(item_id)
        return {
            "ts": ts,
            "lowest": [self._eur(c) for c in cents],
            "buy": buy_eur,
        }

    @staticmethod
    def parse_qty(qty_raw: str) -> int | None:
        raw = (qty_raw or "").strip()
        if not raw:
            return None
        try:
            return max(1, int(raw))
        except ValueError:
            return None

    def parse_buy_to_cents(self, buy_raw: str) -> int | None:
        raw = (buy_raw or "").strip().replace(",", ".")
        if not raw:
            return None
        try:
            return int(round(float(raw) * 100))
        except ValueError:
            return None

    def add_item(
        self,
        steam_url: str,
        name_input: str,
        buy_input: str,
        item_type: str = "inventory",
        qty_input: str = "",
    ) -> tuple[int | None, str | None, dict]:
        mh = self.steam.parse_market_hash_from_url(steam_url)
        if not mh:
            return None, "Bitte eine gueltige Steam-Market-URL angeben.", {
                "display_name": name_input,
                "steam_url": steam_url,
                "buy_eur": buy_input,
            }

        disp, icon, cat = self.steam.fetch_meta_for_hash(mh)
        if name_input:
            disp = name_input.strip()
        buy_cents = self.parse_buy_to_cents(buy_input) if item_type == "inventory" else None

        quantity = self.parse_qty(qty_input) or 1
        new_id = self.repo.insert_item(disp, mh, buy_cents, icon, cat, item_type=item_type, quantity=quantity)
        current = self.steam.fetch_price_cents(mh)
        if current is not None:
            self.repo.insert_price_snapshot(new_id, current)
        return new_id, None, {}

    def update_item(
        self,
        item_id: int,
        name_in: str,
        steam_url: str,
        buy_input: str,
        category_in: str | None,
        icon_input: str | None,
        item_type_in: str | None = None,
        qty_input: str = "",
    ) -> bool:
        row = self.repo.get_item_with_latest_price(item_id)
        if row is None:
            return False

        display_name = row.get("display_name") or ""
        market_hash = row.get("market_hash") or ""
        icon_url = row.get("icon_url")
        category = category_in or row.get("category")
        item_type = item_type_in if item_type_in in ("inventory", "tracking") else None

        if steam_url:
            mh_new = self.steam.parse_market_hash_from_url(steam_url)
            if mh_new:
                market_hash = mh_new
                auto_name, auto_icon, auto_cat = self.steam.fetch_meta_for_hash(market_hash)
                display_name = auto_name
                icon_url = auto_icon
                if not category_in:
                    category = auto_cat

        if name_in:
            display_name = name_in.strip()

        if icon_input is not None and icon_input.strip() != "":
            icon_url = icon_input.strip()

        buy_cents = self.parse_buy_to_cents(buy_input)
        quantity = self.parse_qty(qty_input)
        self.repo.update_item(
            item_id, display_name, market_hash, buy_cents, category, icon_url,
            item_type=item_type, quantity=quantity,
        )
        return True

    def promote_to_inventory(self, item_id: int, buy_input: str) -> bool:
        row = self.repo.get_item_with_latest_price(item_id)
        if row is None:
            return False
        buy_cents = self.parse_buy_to_cents(buy_input)
        self.repo.promote_to_inventory(item_id, buy_cents)
        return True

    def check_and_fire_alerts(self) -> None:
        items = self.repo.get_items_with_active_alerts()
        for row in items:
            cur_c = row.get("current_price_cents")
            if cur_c is None:
                continue
            threshold = float(row["threshold_net_eur"])
            above = bool(int(row.get("above_threshold") or 0))
            item_type = row.get("item_type") or "inventory"

            if item_type == "inventory":
                net_price = cur_c * (1 - FEE_RATE) / 100.0
                triggered = net_price >= threshold if above else net_price <= threshold
            else:
                gross_price = cur_c / 100.0
                triggered = gross_price <= threshold if not above else gross_price >= threshold

            if triggered:
                item_name = row.get("display_name") or f"Item #{row['id']}"
                if self.telegram:
                    if item_type == "inventory":
                        net_eur = cur_c * (1 - FEE_RATE) / 100.0
                        direction = "≥" if above else "≤"
                        msg = (
                            f"🔔 <b>{html.escape(item_name)}</b>\n"
                            f"Verkaufszeitpunkt: Netto {net_eur:.2f} EUR {direction} {threshold:.2f} EUR\n"
                            f"Marktpreis (brutto): {cur_c / 100.0:.2f} EUR"
                        )
                    else:
                        gross_eur = cur_c / 100.0
                        direction = "≤" if not above else "≥"
                        msg = (
                            f"🎯 <b>{html.escape(item_name)}</b>\n"
                            f"Kaufgelegenheit: {gross_eur:.2f} EUR {direction} {threshold:.2f} EUR"
                        )
                    self.telegram.send(msg)
                self.repo.fire_alert(int(row["id"]))

    def refresh_item_price(self, item_id: int) -> bool:
        row = self.repo.get_item_with_latest_price(item_id)
        if row is None:
            return False
        mh = row.get("market_hash") or ""
        if not mh:
            return False
        cents = self.steam.fetch_price_cents(mh)
        if cents is not None:
            self.repo.insert_price_snapshot(item_id, cents)
            return True
        return False

    def refresh_all_active_prices(self) -> tuple[int, int]:
        rows = self.repo.list_items_with_latest_price()
        updated = 0
        skipped = 0
        first = True
        for row in rows:
            if int(row.get("is_active") or 1) != 1:
                continue
            item_id = int(row["id"])
            mh = (row.get("market_hash") or "").strip()
            if not mh:
                skipped += 1
                continue
            if not first:
                time.sleep(3)
            first = False
            cents = self.steam.fetch_price_cents(mh)
            if cents is None:
                skipped += 1
                if self.steam.was_rate_limited:
                    break
                continue
            self.repo.insert_price_snapshot(item_id, cents)
            updated += 1
        return updated, skipped
