from fastapi import FastAPI

from config.logging_config import configure_logging
from config.settings import get_settings
from src.aerial_housing_detection.api.routes.concessionaria_real import (
    router as concessionaria_real_router,
)
from src.aerial_housing_detection.api.routes.demo_realistic import (
    router as demo_realistic_router,
)
from src.aerial_housing_detection.api.routes.detection import router as detection_router
from src.aerial_housing_detection.api.routes.grid_aggregation import (
    router as grid_aggregation_router,
)
from src.aerial_housing_detection.api.routes.health import router as health_router
from src.aerial_housing_detection.api.routes.losses import router as losses_router
from src.aerial_housing_detection.api.routes.operational_search import (
    router as operational_search_router,
)
from src.aerial_housing_detection.api.routes.report import router as report_router
from src.aerial_housing_detection.api.routes.roof_upload import (
    router as roof_upload_router,
)
from src.aerial_housing_detection.api.routes.socioenergy import (
    router as socioenergy_router,
)
from src.aerial_housing_detection.api.routes.web_app import (
    router as web_app_router,
)
from src.aerial_housing_detection.api.routes.web_app import (
    static_files as web_static_files,
)
from src.aerial_housing_detection.api.routes.web_auth import router as web_auth_router


def create_app() -> FastAPI:
    """Create FastAPI application."""
    settings = get_settings()
    configure_logging()

    app = FastAPI(
        title="Aerial Housing Detection",
        description="API para estimativa de residências por imagem aérea.",
        version=settings.app_version,
    )

    app.include_router(health_router)
    app.include_router(detection_router)
    app.include_router(report_router)
    app.include_router(losses_router)
    app.include_router(socioenergy_router)
    app.include_router(grid_aggregation_router)
    app.include_router(operational_search_router)
    app.include_router(roof_upload_router)
    app.include_router(web_app_router)
    app.mount("/app/static", web_static_files, name="app-static")
    app.include_router(web_auth_router)
    app.include_router(demo_realistic_router)
    app.include_router(concessionaria_real_router)
    return app


app = create_app()
