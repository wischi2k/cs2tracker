from __future__ import annotations

from dataclasses import asdict

from app.domain.constants import STEAM_FEE_RATE
from app.domain.models import ItemView
from app.infrastructure.steam_client import SteamClient
from app.repositories.item_repository import ItemRepository
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
    def __init__(self, repo: ItemRepository, steam: SteamClient) -> None:
        self.repo = repo
        self.steam = steam

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
        net_c = None if cur_c is None else int(round(cur_c * (1 - STEAM_FEE_RATE)))
        category = row.get("category")
        if not category:
            category = self._infer_category((row.get("market_hash") or row.get("display_name") or ""))
        return ItemView(
            id=int(row["id"]),
            name=row.get("display_name") or "",
            icon=row.get("icon_url"),
            icon_updated_at=int(row.get("icon_updated_at") or 0),
            cat=category,
            active=int(row.get("is_active") or 1),
            buy=self._eur(buy_c),
            cur=self._eur(cur_c),
            net=self._eur(net_c),
            diff_g=None if buy_c is None or cur_c is None else self._eur(cur_c - buy_c),
            diff_n=None if buy_c is None or cur_c is None else self._eur(net_c - buy_c),
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
        buy_cents = self.parse_buy_to_cents(buy_input)

        new_id = self.repo.insert_item(disp, mh, buy_cents, icon, cat)
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
    ) -> bool:
        row = self.repo.get_item_with_latest_price(item_id)
        if row is None:
            return False

        display_name = row.get("display_name") or ""
        market_hash = row.get("market_hash") or ""
        icon_url = row.get("icon_url")
        category = category_in or row.get("category")

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
        self.repo.update_item(item_id, display_name, market_hash, buy_cents, category, icon_url)
        return True

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
        for row in rows:
            if int(row.get("is_active") or 1) != 1:
                continue
            item_id = int(row["id"])
            mh = (row.get("market_hash") or "").strip()
            if not mh:
                skipped += 1
                continue
            cents = self.steam.fetch_price_cents(mh)
            if cents is None:
                skipped += 1
                continue
            self.repo.insert_price_snapshot(item_id, cents)
            updated += 1
        return updated, skipped
