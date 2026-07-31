from __future__ import annotations

from app.infrastructure.steam_client import SteamClient
from app.repositories.config_repository import ConfigRepository
from app.repositories.item_repository import ItemRepository


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

    def build_preview(self, steam_input: str) -> tuple[dict | None, str | None]:
        steam_id = self.steam.resolve_steam_id(steam_input)
        if not steam_id:
            return None, "SteamID nicht erkannt. Bitte SteamID64, Profil-URL oder Vanity-Namen angeben."

        inv_items, err = self.steam.fetch_inventory(steam_id)
        if err:
            return None, err

        self.config_repo.set_value("steam_inventory_input", steam_input.strip())

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
