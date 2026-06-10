from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

WEB_STATIC_DIR = Path(__file__).resolve().parents[2] / "web" / "static"
REPORTS_DIR = Path("reports")
TRANSFORMER_MAP_PATH = REPORTS_DIR / "transformer_operational_map.html"

router = APIRouter(tags=["web-app"])
static_files = StaticFiles(directory=WEB_STATIC_DIR)


@router.get("/", include_in_schema=False)
def redirect_to_login() -> RedirectResponse:
    return RedirectResponse(url="/login")


@router.get("/login", include_in_schema=False)
def serve_login() -> FileResponse:
    return FileResponse(WEB_STATIC_DIR / "login.html")


@router.get("/app", include_in_schema=False)
def serve_app() -> FileResponse:
    return FileResponse(WEB_STATIC_DIR / "index.html")

@router.get("/app/synthetic-loss-agent", include_in_schema=False)
def serve_synthetic_loss_agent_dashboard() -> FileResponse:
    return FileResponse(WEB_STATIC_DIR / "synthetic_loss_agent.html")


@router.get("/app/map", include_in_schema=False)
def serve_operational_map() -> FileResponse:
    if not TRANSFORMER_MAP_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Mapa operacional ainda não foi gerado. "
                "Execute a geração do mapa antes de acessar esta página."
            ),
        )

    return FileResponse(TRANSFORMER_MAP_PATH)
