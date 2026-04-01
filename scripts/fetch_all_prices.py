from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.infrastructure.steam_client import SteamClient
from app.repositories.item_repository import ItemRepository


def main() -> int:
    repo = ItemRepository()
    steam = SteamClient()

    rows = repo.list_items_with_latest_price()
    active_rows = [r for r in rows if int(r.get("is_active") or 1) == 1]

    ok = 0
    skipped = 0
    for row in active_rows:
        item_id = int(row["id"])
        market_hash = (row.get("market_hash") or "").strip()
        if not market_hash:
            skipped += 1
            continue

        cents = steam.fetch_price_cents(market_hash)
        if cents is None:
            skipped += 1
            continue

        repo.insert_price_snapshot(item_id, cents)
        ok += 1

    print(f"Updated: {ok}, skipped: {skipped}, active items: {len(active_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
