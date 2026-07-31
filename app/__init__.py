import os

from flask import Flask
from flask_wtf import CSRFProtect

from app.config import Config
from app.infrastructure.steam_client import SteamClient
from app.infrastructure.telegram_client import TelegramClient
from app.repositories.config_repository import ConfigRepository
from app.repositories.item_repository import ItemRepository
from app.services.import_service import ImportService
from app.services.item_service import ItemService
from app.services.price_scheduler_service import PriceSchedulerService
from app.services.setup_service import SetupService
from app.services.summary_service import SummaryService
from app.web.routes_health import register_health_routes
from app.web.routes_import import register_import_routes
from app.web.routes_items import register_item_routes
from app.web.routes_setup import register_setup_routes


def create_app() -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(Config)
    CSRFProtect(app)

    repo = ItemRepository()
    config_repo = ConfigRepository()
    steam = SteamClient()
    telegram = TelegramClient(config_repo=config_repo)
    service = ItemService(repo=repo, steam=steam, telegram=telegram)
    summary_service = SummaryService(repo=repo)
    setup_service = SetupService(config_repo=config_repo)
    import_service = ImportService(repo=repo, steam=steam, config_repo=config_repo)
    scheduler = PriceSchedulerService(
        config_repo=config_repo,
        item_service=service,
        summary_service=summary_service,
        telegram=telegram,
        setup_service=setup_service,
        app=app,
    )

    repo.ensure_schema()
    config_repo.ensure_schema()
    setup_service.ensure_default_config()

    register_health_routes(app, setup_service=setup_service)
    register_item_routes(app, service=service, repo=repo, telegram=telegram, summary_service=summary_service)
    register_setup_routes(app, setup_service=setup_service, telegram=telegram)
    register_import_routes(app, import_service=import_service)

    should_start_scheduler = (not app.config["DEBUG"]) or os.getenv("WERKZEUG_RUN_MAIN") == "true"
    if should_start_scheduler:
        scheduler.start()
    app.extensions["price_scheduler"] = scheduler

    app.secret_key = app.config["SECRET_KEY"]
    return app
