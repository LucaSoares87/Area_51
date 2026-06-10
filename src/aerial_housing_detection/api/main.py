from fastapi import FastAPI

import src.aerial_housing_detection.api.routes.concessionaria_real  # pyright: ignore[reportMissingImports]
import src.aerial_housing_detection.api.routes.demo_realistic  # type: ignore
import src.aerial_housing_detection.api.routes.operational_features  # pyright: ignore[reportMissingImports]
import src.aerial_housing_detection.api.routes.operational_search  # pyright: ignore[reportMissingImports]
import src.aerial_housing_detection.api.routes.report
import src.aerial_housing_detection.api.routes.roof_upload  # pyright: ignore[reportMissingImports]
import src.aerial_housing_detection.api.routes.synthetic_feeder_operational  # type: ignore
import src.aerial_housing_detection.api.routes.synthetic_loss_agent  # type: ignore
import src.aerial_housing_detection.api.routes.web_app  # type: ignore
import src.aerial_housing_detection.api.routes.web_auth
from config.logging_config import configure_logging
from config.settings import get_settings
from src.aerial_housing_detection.api.routes.detection import router as detection_router
from src.aerial_housing_detection.api.routes.grid_aggregation import (
    router as grid_aggregation_router,
)
from src.aerial_housing_detection.api.routes.health import router as health_router
from src.aerial_housing_detection.api.routes.losses import router as losses_router
from src.aerial_housing_detection.api.routes.socioenergy import (
    router as socioenergy_router,
)


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
    app.include_router(src.aerial_housing_detection.api.routes.report.router)
    app.include_router(losses_router)
    app.include_router(socioenergy_router)
    app.include_router(grid_aggregation_router)
    app.include_router(
        src.aerial_housing_detection.api.routes.operational_search.router
    )
    app.include_router(
        src.aerial_housing_detection.api.routes.operational_features.router
    )
    app.include_router(src.aerial_housing_detection.api.routes.roof_upload.router)
    app.include_router(src.aerial_housing_detection.api.routes.web_app.router)
    app.mount(
        "/app/static",
        src.aerial_housing_detection.api.routes.web_app.static_files,
        name="app-static",
    )
    app.include_router(src.aerial_housing_detection.api.routes.web_auth.router)
    app.include_router(src.aerial_housing_detection.api.routes.demo_realistic.router)
    app.include_router(
        src.aerial_housing_detection.api.routes.concessionaria_real.router
    )
    app.include_router(
        src.aerial_housing_detection.api.routes.synthetic_loss_agent.router
    )
    app.include_router(src.aerial_housing_detection.api.routes.synthetic_feeder_operational.router)
    return app


app = create_app()
