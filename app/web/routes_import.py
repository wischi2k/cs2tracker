from __future__ import annotations

from flask import flash, redirect, render_template, request, url_for

from app.services.import_service import ImportService


def register_import_routes(app, import_service: ImportService) -> None:
    @app.get("/import")
    def import_inventory():
        return render_template(
            "import.html",
            steam_input=import_service.get_saved_steam_input(),
            preview=None,
            error=None,
            import_status=import_service.get_import_status(),
        )

    @app.post("/import/preview")
    def import_preview():
        steam_input = (request.form.get("steam_input") or "").strip()
        preview, error = import_service.build_preview(steam_input)
        return render_template(
            "import.html",
            steam_input=steam_input,
            preview=preview,
            error=error,
            import_status=import_service.get_import_status(),
        )

    @app.post("/import/apply")
    def import_apply():
        count = int(request.form.get("row_count") or 0)
        rows = []
        for i in range(count):
            rows.append(
                {
                    "market_hash": request.form.get(f"mh_{i}", ""),
                    "name": request.form.get(f"name_{i}", ""),
                    "icon": request.form.get(f"icon_{i}", ""),
                    "category": request.form.get(f"cat_{i}", ""),
                    "qty": request.form.get(f"qty_{i}", "1"),
                    "selected": request.form.get(f"sel_{i}") == "on",
                }
            )
        result = import_service.apply_selection(rows)

        parts = []
        if result["added"]:
            parts.append(f"{result['added']} neu")
        if result["reactivated"]:
            parts.append(f"{result['reactivated']} reaktiviert")
        if result["deactivated"]:
            parts.append(f"{result['deactivated']} deaktiviert")
        if result["qty_updated"]:
            parts.append(f"{result['qty_updated']} Stueckzahl aktualisiert")
        if parts:
            msg = "Inventar-Abgleich uebernommen: " + ", ".join(parts) + "."
            if result["added"] or result["reactivated"]:
                msg += " Preise werden im Hintergrund geladen."
            flash(msg, "success")
        else:
            flash("Keine Aenderungen — Auswahl entsprach dem aktuellen Stand.", "info")
        return redirect(url_for("index"))
