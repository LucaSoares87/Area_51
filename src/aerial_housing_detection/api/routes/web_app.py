from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

WEB_STATIC_DIR = (
    Path(__file__).resolve().parents[2] / "web" / "static"
)

router = APIRouter(tags=["web-app"])
static_files = StaticFiles(directory=WEB_STATIC_DIR)


@router.get("/app", include_in_schema=False)
def serve_app() -> FileResponse:
    return FileResponse(WEB_STATIC_DIR / "index.html")
