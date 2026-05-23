from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.auth.middleware import register_middlewares
from src.auth.router import router as auth_router
from src.detect.config import detect_settings
from src.detect.router import router as detect_router
from src.lgpd.config import lgpd_settings
from src.lgpd.router import router as lgpd_router
from src.monitoring.config import monitoring_settings
from src.monitoring.router import router as monitoring_router


def _ensure_directories() -> None:
    for path in [
        detect_settings.uploads_dir,
        detect_settings.results_dir,
        monitoring_settings.metrics_dir,
        lgpd_settings.audit_log_dir,
        lgpd_settings.report_output_dir,
    ]:
        path.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ensure_directories()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Aerial Housing Detection",
        description="Deteccao de habitacoes irregulares em imagens aereas",
        version="1.0.0",
        lifespan=lifespan,
    )

    register_middlewares(app)

    app.include_router(auth_router)
    app.include_router(detect_router)
    app.include_router(monitoring_router)
    app.include_router(lgpd_router)

    @app.get("/health", tags=["infra"])
    async def health():
        return {"status": "healthy"}

    return app
