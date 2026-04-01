import os


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "cs2tracker_dev_secret_change_me")
    DATABASE_PATH = os.getenv("CS2_DB_PATH", "cs2_prices.sqlite")
    DEBUG = os.getenv("FLASK_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}
    HOST = os.getenv("FLASK_HOST", "127.0.0.1")
    PORT = int(os.getenv("FLASK_PORT", "5000"))
