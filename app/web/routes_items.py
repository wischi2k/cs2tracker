from __future__ import annotations

import html
import time

from flask import flash, jsonify, redirect, render_template, request, url_for

from app.infrastructure.telegram_client import TelegramClient
from app.repositories.item_repository import ItemRepository
from app.services.item_service import CATEGORIES, ItemService


def register_item_routes(app, service: ItemService, repo: ItemRepository, telegram: TelegramClient) -> None:
    def _redirect_index(cat: str | None = None):
        kwargs = {"cat": cat} if cat else {}
        return redirect(url_for("index", **kwargs))

    def index():
        sel_cat = request.args.get("cat", "Alle")
        items, cats = service.list_items(sel_cat)
        return render_template(
            "index.html",
            categories=cats,
            items=items,
            selected=None,
            now_ts=int(time.time()),
        )

    def item(item_id: int):
        sel_cat = request.args.get("cat", "Alle")
        selected_item = service.get_item_view(item_id)
        if selected_item is None:
            return _redirect_index(sel_cat)

        items, cats = service.list_items(sel_cat)
        chart = service.get_chart_payload(item_id, selected_item["buy"])
        alert_th = repo.get_alert_threshold(item_id)

        return render_template(
            "index.html",
            categories=cats,
            items=items,
            selected={"it": selected_item, "chart": chart, "alert_th": alert_th},
            now_ts=int(time.time()),
        )

    def api_item(item_id: int):
        selected_item = service.get_item_view(item_id)
        if selected_item is None:
            return jsonify({"ok": False}), 404
        return jsonify(service.get_chart_payload(item_id, selected_item["buy"]))

    def add_get():
        sel_cat = request.args.get("cat", "Alle")
        dummy = {
            "id": None,
            "display_name": "",
            "steam_url": "",
            "buy": None,
            "buy_eur": "",
            "category": (sel_cat if sel_cat != "Alle" else ""),
            "is_active": 1,
        }
        return render_template("add.html", it=dummy, categories=CATEGORIES, error=None)

    def add_post():
        name_in = (request.form.get("name") or "").strip()
        steam_url = (request.form.get("steam_url") or "").strip()
        buy_raw = (request.form.get("buy") or request.form.get("buy_eur") or "").strip()

        new_id, error, payload = service.add_item(steam_url, name_in, buy_raw)
        if error:
            return render_template(
                "add.html",
                it={
                    "display_name": payload.get("display_name", ""),
                    "steam_url": payload.get("steam_url", ""),
                    "buy": None,
                    "buy_eur": payload.get("buy_eur", ""),
                    "category": "",
                    "is_active": 1,
                },
                categories=CATEGORIES,
                error=error,
            )
        return redirect(url_for("item", item_id=new_id))

    def edit_item_get(item_id: int):
        sel_cat = request.args.get("cat", "Alle")
        item_view = service.get_item_view(item_id)
        if item_view is None:
            return _redirect_index(sel_cat)

        row = repo.get_item_with_latest_price(item_id)
        it = {
            "id": item_view["id"],
            "display_name": row.get("display_name") if row else item_view["name"],
            "market_hash": row.get("market_hash") if row else "",
            "buy": item_view["buy"],
            "icon_url": row.get("icon_url") if row else None,
            "category": row.get("category") if row else None,
            "active": int(row.get("is_active") if row else 1),
        }
        return render_template("edit.html", it=it, sel_cat=sel_cat, categories=CATEGORIES)

    def update_item(item_id: int):
        sel_cat = request.args.get("cat")
        ok = service.update_item(
            item_id=item_id,
            name_in=(request.form.get("name") or "").strip(),
            steam_url=(request.form.get("steam_url") or "").strip(),
            buy_input=(request.form.get("buy") or request.form.get("buy_eur") or "").strip(),
            category_in=((request.form.get("category") or "").strip() or None),
            icon_input=((request.form.get("icon_url") or "").strip() or None),
        )
        if not ok:
            return _redirect_index(sel_cat)
        return redirect(url_for("item", item_id=item_id, **({"cat": sel_cat} if sel_cat else {})))

    def set_item_status(item_id: int):
        sel_cat = request.args.get("cat")
        repo.toggle_item_status(item_id)
        return redirect(url_for("edit_item_get", item_id=item_id, **({"cat": sel_cat} if sel_cat else {})))

    def delete_item(item_id: int):
        repo.delete_item(item_id)
        return _redirect_index(request.args.get("cat"))

    def refresh_item(item_id: int):
        sel_cat = request.args.get("cat")
        ok = service.refresh_item_price(item_id)
        if ok:
            flash("Preis wurde aktualisiert.", "success")
        else:
            flash("Aktuell kein Preis abrufbar.", "info")
        return redirect(url_for("item", item_id=item_id, **({"cat": sel_cat} if sel_cat else {})))

    def set_alert(item_id: int):
        raw = (request.form.get("threshold") or "").strip().replace(",", ".")
        try:
            th = float(raw) if raw else None
        except ValueError:
            th = None

        item_name = repo.get_item_name(item_id) or f"Item #{item_id}"
        if th is None:
            repo.delete_alert_threshold(item_id)
            flash(f"Preisalarm fuer {html.escape(item_name)} wurde geloescht.", "info")
        else:
            repo.upsert_alert_threshold(item_id, th)
            flash(f"Preisalarm fuer {html.escape(item_name)} eingerichtet: ab EUR {th:.2f} (Netto).", "success")
            telegram.send(f"<b>{html.escape(item_name)}</b> - ab EUR {th:.2f}")

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return ("OK", 200)
        return redirect(url_for("item", item_id=item_id, **({"cat": request.args.get("cat")} if request.args.get("cat") else {})))

    app.add_url_rule("/", endpoint="index", view_func=index, methods=["GET"])
    app.add_url_rule("/item/<int:item_id>", endpoint="item", view_func=item, methods=["GET"])
    app.add_url_rule("/api/item/<int:item_id>", endpoint="api_item", view_func=api_item, methods=["GET"])

    app.add_url_rule("/add", endpoint="add", view_func=add_get, methods=["GET"])
    app.add_url_rule("/add", endpoint="add_post", view_func=add_post, methods=["POST"])
    app.add_url_rule("/add-item", endpoint="add_item", view_func=add_post, methods=["POST"])

    app.add_url_rule("/item/<int:item_id>/edit", endpoint="edit_item_get", view_func=edit_item_get, methods=["GET"])
    app.add_url_rule("/item/<int:item_id>/edit", endpoint="update_item", view_func=update_item, methods=["POST"])
    app.add_url_rule("/item/<int:item_id>/status", endpoint="set_item_status", view_func=set_item_status, methods=["POST"])
    app.add_url_rule("/item/<int:item_id>/delete", endpoint="delete_item", view_func=delete_item, methods=["POST"])
    app.add_url_rule("/item/<int:item_id>/refresh", endpoint="refresh_item", view_func=refresh_item, methods=["POST"])

    app.add_url_rule("/alert/<int:item_id>", endpoint="set_alert", view_func=set_alert, methods=["POST"])
