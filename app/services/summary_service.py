from __future__ import annotations

import time
from dataclasses import dataclass

from app.domain.constants import STEAM_FEE_RATE
from app.domain.wear import append_wear_condition
from app.repositories.item_repository import ItemRepository


@dataclass
class SummaryPayload:
    text_html: str
    considered_items: int


class SummaryService:
    def __init__(self, repo: ItemRepository) -> None:
        self.repo = repo

    @staticmethod
    def _net_eur_from_cents(cents: int) -> float:
        return (cents / 100.0) * (1 - STEAM_FEE_RATE)

    def build_summary(self, interval_days: int) -> SummaryPayload:
        now_ts = int(time.time())
        start_ts = now_ts - int(interval_days) * 86400

        all_items = self.repo.list_active_items_basic()
        considered_items = len(all_items)

        inventory_items = [r for r in all_items if (r.get("item_type") or "inventory") == "inventory"]
        tracking_items = [r for r in all_items if (r.get("item_type") or "inventory") == "tracking"]

        movement: list[dict] = []
        valuable: list[dict] = []
        profit_vs_buy: list[dict] = []

        for row in inventory_items:
            item_id = int(row["id"])
            qty = max(1, int(row.get("quantity") or 1))
            name = append_wear_condition(row.get("display_name"), row.get("market_hash")) or f"Item #{item_id}"
            if qty > 1:
                name = f"{name} (x{qty})"

            baseline = self.repo.get_price_at_or_before(item_id, start_ts)
            if baseline is None:
                baseline = self.repo.get_price_at_or_after(item_id, start_ts)
            latest = self.repo.get_latest_price_cents(item_id)

            if latest is not None:
                latest_net = self._net_eur_from_cents(latest) * qty
                valuable.append({"name": name, "latest_net": latest_net})
            else:
                latest_net = None

            buy_cents = row.get("buy_price_cents")
            if latest_net is not None and buy_cents is not None:
                buy_net = self._net_eur_from_cents(int(buy_cents)) * qty
                profit = latest_net - buy_net
                profit_vs_buy.append({"name": name, "profit_net": profit, "latest_net": latest_net, "buy_net": buy_net})

            if baseline is None or latest is None:
                continue

            base_net = self._net_eur_from_cents(baseline) * qty
            if base_net <= 0:
                continue
            latest_net_for_move = self._net_eur_from_cents(latest) * qty
            delta = latest_net_for_move - base_net
            pct = (delta / base_net) * 100.0
            movement.append({"name": name, "base_net": base_net, "latest_net": latest_net_for_move, "delta_net": delta, "pct": pct})

        gainers = sorted([m for m in movement if m["pct"] > 0], key=lambda x: x["pct"], reverse=True)[:3]
        losers = sorted([m for m in movement if m["pct"] < 0], key=lambda x: x["pct"])[:3]
        top_valuable = sorted(valuable, key=lambda x: x["latest_net"], reverse=True)[:3]
        top_profit_vs_buy = sorted(profit_vs_buy, key=lambda x: x["profit_net"], reverse=True)[:3]

        lines: list[str] = []
        lines.append(f"<b>📦 Portfolio-Zusammenfassung</b> (letzte {int(interval_days)} Tage)")
        lines.append("")

        lines.append("<b>Top 3 Gewinner (Zeitraum)</b>")
        if gainers:
            for g in gainers:
                lines.append(
                    f"• <b>{g['name']}</b> {g['pct']:+.2f}% "
                    f"({g['latest_net']:.2f} EUR / {g['base_net']:.2f} EUR; {g['delta_net']:+.2f} EUR)"
                )
        else:
            lines.append("• – (keine positiven Bewegungen)")

        if losers:
            lines.append("")
            lines.append("<b>Top 3 Verlierer (Zeitraum)</b>")
            for l in losers:
                lines.append(
                    f"• <b>{l['name']}</b> {l['pct']:+.2f}% "
                    f"({l['latest_net']:.2f} EUR / {l['base_net']:.2f} EUR; {l['delta_net']:+.2f} EUR)"
                )

        lines.append("")
        lines.append("<b>Top 3 wertvollste Items (Netto)</b>")
        if top_valuable:
            for v in top_valuable:
                lines.append(f"• <b>{v['name']}</b> {v['latest_net']:.2f} EUR")
        else:
            lines.append("• – (keine Preisdaten)")

        lines.append("")
        lines.append("<b>Top 3 Gewinn vs. Kaufpreis</b>")
        if top_profit_vs_buy:
            for p in top_profit_vs_buy:
                lines.append(
                    f"• <b>{p['name']}</b> {p['profit_net']:+.2f} EUR "
                    f"(aktuell {p['latest_net']:.2f} EUR / Kauf {p['buy_net']:.2f} EUR)"
                )
        else:
            lines.append("• – (keine Kaufpreise hinterlegt)")

        if tracking_items:
            lines.append("")
            lines.append("<b>👁 Beobachtungsliste</b>")
            for row in tracking_items:
                item_id = int(row["id"])
                name = append_wear_condition(row.get("display_name"), row.get("market_hash")) or f"Item #{item_id}"
                latest = self.repo.get_latest_price_cents(item_id)
                price_str = f"{latest / 100.0:.2f} EUR" if latest is not None else "kein Preis"
                threshold = row.get("threshold_net_eur")
                above = row.get("above_threshold")
                if threshold is not None:
                    direction = "≥" if above else "≤"
                    lines.append(f"• <b>{name}</b> — {price_str} (Ziel: {direction} {float(threshold):.2f} EUR)")
                else:
                    lines.append(f"• <b>{name}</b> — {price_str}")

        lines.append("")
        lines.append(f"<i>Erstellt: {time.strftime('%Y-%m-%d %H:%M:%S')} (Serverzeit)</i>")
        lines.append(f"<i>Inventar: {len(inventory_items)} Items · Beobachtungsliste: {len(tracking_items)} Items</i>")

        return SummaryPayload(text_html="\n".join(lines), considered_items=considered_items)

    def compute_portfolio_totals(self) -> dict[str, int | None]:
        """Aktuelle qty-gewichtete Portfolio-Summen (Cent) ueber aktive Inventar-Items."""
        rows = self.repo.list_active_items_basic()
        total_gross = 0
        total_net = 0
        total_buy = 0
        have_buy = False
        count = 0
        for row in rows:
            if (row.get("item_type") or "inventory") != "inventory":
                continue
            item_id = int(row["id"])
            qty = max(1, int(row.get("quantity") or 1))
            latest = self.repo.get_latest_price_cents(item_id)
            if latest is not None:
                total_gross += latest * qty
                total_net += int(round(latest * (1 - STEAM_FEE_RATE))) * qty
            buy_cents = row.get("buy_price_cents")
            if buy_cents is not None:
                total_buy += int(buy_cents) * qty
                have_buy = True
            count += 1
        return {
            "total_gross_cents": total_gross,
            "total_net_cents": total_net,
            "total_buy_cents": total_buy if have_buy else None,
            "item_count": count,
        }

    def record_portfolio_snapshot(self) -> None:
        totals = self.compute_portfolio_totals()
        if not totals["item_count"]:
            return
        self.repo.insert_portfolio_snapshot(
            total_gross_cents=int(totals["total_gross_cents"] or 0),
            total_net_cents=int(totals["total_net_cents"] or 0),
            total_buy_cents=totals["total_buy_cents"],
            item_count=int(totals["item_count"] or 0),
        )

    def get_portfolio_chart_payload(self) -> dict:
        rows = self.repo.get_portfolio_series()
        return {
            "ts": [int(r["ts"]) for r in rows],
            "gross": [r["total_gross_cents"] / 100.0 for r in rows],
            "net": [r["total_net_cents"] / 100.0 for r in rows],
            "buy": [None if r["total_buy_cents"] is None else r["total_buy_cents"] / 100.0 for r in rows],
        }
