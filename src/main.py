from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.auth.router import router as auth_router
from src.detect.router import router as detect_router
from src.detect.config import detect_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Area 51 - Startup")
    detect_settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    detect_settings.results_dir.mkdir(parents=True, exist_ok=True)
    yield
    print("Area 51 - Shutdown")


app = FastAPI(
    title="Area 51 - Identificacao Aerea",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor", "type": type(exc).__name__},
    )


app.include_router(auth_router)
app.include_router(detect_router)


@app.get("/health", tags=["infra"])
async def health():
    return {"status": "ok", "service": "area-51", "mock_inference": detect_settings.mock_inference}


@app.get("/", tags=["infra"])
async def root():
    return {"service": "Area 51", "docs": "/docs", "health": "/health"}
