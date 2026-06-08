import csv
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from src.aerial_housing_detection.ml.synthetic_loss_classifier import (
    DB_PATH,
    SyntheticLossClassifier,
)
from src.aerial_housing_detection.ml.synthetic_loss_heatmap import (
    SyntheticLossHeatmapBuilder,
)
from src.aerial_housing_detection.ml.synthetic_loss_map import (
    SyntheticLossMapBuilder,
)

router = APIRouter(prefix="/synthetic-loss-agent", tags=["Synthetic Loss Agent"])

METRICS_PATH = Path("reports/synthetic_loss_classifier_metrics.json")
RANKING_PATH = Path("reports/synthetic_loss_classifier_ranking.csv")
TRANSFORMER_HEATMAP_PATH = Path("reports/synthetic_loss_heatmap_transformers.csv")
FEEDER_HEATMAP_PATH = Path("reports/synthetic_loss_heatmap_feeders.csv")
HEATMAP_SUMMARY_PATH = Path("reports/synthetic_loss_heatmap_summary.json")
MAP_PATH = Path("reports/synthetic_loss_heatmap_map.html")


@router.get("/health")
def synthetic_loss_agent_health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "synthetic_loss_agent",
        "description": "API sintética do agente de perdas",
    }


@router.post("/run")
def run_synthetic_loss_agent() -> dict[str, Any]:
    classifier_result = _build_classifier().run()
    heatmap_result = _build_heatmap_builder().run()
    map_result = _build_map_builder().run()

    return {
        "status": "success",
        "classifier": {
            "total_rows": classifier_result.total_rows,
            "positive_rows": classifier_result.positive_rows,
            "precision_at_10": classifier_result.precision_at_10,
            "precision_at_50": classifier_result.precision_at_50,
            "recall_at_50": classifier_result.recall_at_50,
            "metrics_path": classifier_result.metrics_path,
            "ranking_path": classifier_result.ranking_path,
        },
        "heatmap": {
            "transformer_rows": heatmap_result.transformer_rows,
            "feeder_rows": heatmap_result.feeder_rows,
            "high_heat_transformers": heatmap_result.high_heat_transformers,
            "high_heat_feeders": heatmap_result.high_heat_feeders,
            "transformer_heatmap_path": heatmap_result.transformer_heatmap_path,
            "feeder_heatmap_path": heatmap_result.feeder_heatmap_path,
            "summary_path": heatmap_result.summary_path,
        },
        "map": {
            "transformer_points": map_result.transformer_points,
            "feeder_points": map_result.feeder_points,
            "high_heat_transformers": map_result.high_heat_transformers,
            "high_heat_feeders": map_result.high_heat_feeders,
            "map_path": map_result.map_path,
        },
    }


@router.get("/metrics")
def get_synthetic_loss_metrics() -> dict[str, Any]:
    if not METRICS_PATH.exists():
        _build_classifier().run()

    return _read_json(METRICS_PATH)


@router.get("/ranking")
def get_synthetic_loss_ranking(limit: int = 50) -> dict[str, Any]:
    if not RANKING_PATH.exists():
        _build_classifier().run()

    rows = _read_csv(RANKING_PATH)

    return {
        "total_rows": len(rows),
        "limit": limit,
        "items": rows[: max(limit, 0)],
    }


@router.get("/heatmap/transformers")
def get_transformer_heatmap(limit: int = 200) -> dict[str, Any]:
    if not TRANSFORMER_HEATMAP_PATH.exists():
        _build_heatmap_builder().run()

    rows = _read_csv(TRANSFORMER_HEATMAP_PATH)

    return {
        "total_rows": len(rows),
        "limit": limit,
        "items": rows[: max(limit, 0)],
    }


@router.get("/heatmap/feeders")
def get_feeder_heatmap(limit: int = 200) -> dict[str, Any]:
    if not FEEDER_HEATMAP_PATH.exists():
        _build_heatmap_builder().run()

    rows = _read_csv(FEEDER_HEATMAP_PATH)

    return {
        "total_rows": len(rows),
        "limit": limit,
        "items": rows[: max(limit, 0)],
    }


@router.get("/heatmap/summary")
def get_heatmap_summary() -> dict[str, Any]:
    if not HEATMAP_SUMMARY_PATH.exists():
        _build_heatmap_builder().run()

    return _read_json(HEATMAP_SUMMARY_PATH)


@router.get("/map", response_class=HTMLResponse)
def get_synthetic_loss_map() -> HTMLResponse:
    if not MAP_PATH.exists():
        _build_map_builder().run()

    if not MAP_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Mapa sintético de perdas não encontrado",
        )

    return HTMLResponse(MAP_PATH.read_text(encoding="utf-8"))


def _build_classifier() -> SyntheticLossClassifier:
    return SyntheticLossClassifier(
        db_path=DB_PATH,
        metrics_path=METRICS_PATH,
        ranking_path=RANKING_PATH,
    )


def _build_heatmap_builder() -> SyntheticLossHeatmapBuilder:
    return SyntheticLossHeatmapBuilder(
        db_path=DB_PATH,
        transformer_heatmap_path=TRANSFORMER_HEATMAP_PATH,
        feeder_heatmap_path=FEEDER_HEATMAP_PATH,
        summary_path=HEATMAP_SUMMARY_PATH,
    )


def _build_map_builder() -> SyntheticLossMapBuilder:
    return SyntheticLossMapBuilder(
        db_path=DB_PATH,
        map_path=MAP_PATH,
    )


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
