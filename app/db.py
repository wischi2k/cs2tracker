import os
import sqlite3

from flask import current_app, has_app_context


def get_connection() -> sqlite3.Connection:
    db_path = (
        current_app.config["DATABASE_PATH"]
        if has_app_context()
        else os.getenv("CS2_DB_PATH", "cs2_prices.sqlite")
    )
    con = sqlite3.connect(db_path, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA busy_timeout = 30000")
    return con
