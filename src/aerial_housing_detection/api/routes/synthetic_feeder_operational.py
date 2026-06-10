import csv
import json
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from src.aerial_housing_detection.ml.synthetic_feeder_operational import (
    DB_PATH,
    ROUTE_PATH,
    SECTIONS_PATH,
    SUMMARY_PATH,
    SyntheticFeederOperationalBuilder,
)

router = APIRouter(
    prefix="/synthetic-feeder-operational",
    tags=["Synthetic Feeder Operational"],
)


@router.get("/health")
def synthetic_feeder_operational_health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "synthetic_feeder_operational",
        "description": "API sintética operacional de alimentador",
    }


@router.post("/run")
def run_synthetic_feeder_operational() -> dict[str, Any]:
    result = _build_builder().run()

    return {
        "status": "success",
        "database_path": result.database_path,
        "summary_path": result.summary_path,
        "route_path": result.route_path,
        "sections_path": result.sections_path,
        "substations": result.substations,
        "feeders": result.feeders,
        "route_points": result.route_points,
        "reclosers": result.reclosers,
        "mv_customers": result.mv_customers,
        "transformers": result.transformers,
        "sections": result.sections,
    }


@router.get("/summary")
def get_synthetic_feeder_summary() -> dict[str, Any]:
    if not SUMMARY_PATH.exists():
        _build_builder().run()

    return _read_json(SUMMARY_PATH)


@router.get("/route")
def get_synthetic_feeder_route() -> dict[str, Any]:
    if not ROUTE_PATH.exists():
        _build_builder().run()

    rows = _read_csv(ROUTE_PATH)

    return {
        "total_rows": len(rows),
        "items": rows,
    }


@router.get("/sections")
def get_synthetic_feeder_sections() -> dict[str, Any]:
    if not SECTIONS_PATH.exists():
        _build_builder().run()

    rows = _read_csv(SECTIONS_PATH)

    return {
        "total_rows": len(rows),
        "items": rows,
    }


@router.get("/reclosers")
def get_synthetic_feeder_reclosers() -> dict[str, Any]:
    _ensure_database()

    rows = _read_table("synthetic_feeder_reclosers")

    return {
        "total_rows": len(rows),
        "items": rows,
    }


@router.get("/transformers")
def get_synthetic_feeder_transformers(limit: int = 100) -> dict[str, Any]:
    _ensure_database()

    rows = _read_table("synthetic_feeder_transformers")

    return {
        "total_rows": len(rows),
        "limit": limit,
        "items": rows[: max(limit, 0)],
    }


@router.get("/mv-customers")
def get_synthetic_feeder_mv_customers() -> dict[str, Any]:
    _ensure_database()

    rows = _read_table("synthetic_feeder_mv_customers")

    return {
        "total_rows": len(rows),
        "items": rows,
    }


@router.get("/substations")
def get_synthetic_feeder_substations() -> dict[str, Any]:
    _ensure_database()

    rows = _read_table("synthetic_feeder_substations")

    return {
        "total_rows": len(rows),
        "items": rows,
    }


@router.get("/feeders")
def get_synthetic_feeder_feeders() -> dict[str, Any]:
    _ensure_database()

    rows = _read_table("synthetic_feeder_feeders")

    return {
        "total_rows": len(rows),
        "items": rows,
    }


def _build_builder() -> SyntheticFeederOperationalBuilder:
    return SyntheticFeederOperationalBuilder(
        db_path=DB_PATH,
        summary_path=SUMMARY_PATH,
        route_path=ROUTE_PATH,
        sections_path=SECTIONS_PATH,
    )


def _ensure_database() -> None:
    if not DB_PATH.exists():
        _build_builder().run()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Arquivo não encontrado: {path}")

    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Arquivo não encontrado: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return [dict(row) for row in reader]


def _read_table(table_name: str) -> list[dict[str, Any]]:
    if not DB_PATH.exists():
        raise HTTPException(status_code=404, detail="Banco sintético não encontrado")

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row

        if not _table_exists(connection, table_name):
            _build_builder().run()

        rows = connection.execute(f"SELECT * FROM {table_name}").fetchall()

    return [dict(row) for row in rows]


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        """,
        (table_name,),
    ).fetchone()

    return row is not None
