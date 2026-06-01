import csv
import json
from pathlib import Path

from src.aerial_housing_detection.ml.explainability import (
    TransformerRankingExplainer,
    build_ranking_reasons,
)


def test_build_ranking_reasons_returns_auditable_reasons() -> None:
    row = {
        "target_risco_alto": "1",
        "risco_score": "80",
        "consumo_faturado_kwh": "15000",
        "consumo_medio_por_cliente_ligado": "400",
        "percentual_cortado": "0.25",
        "percentual_baixado": "0.12",
        "energia_injetada_total": "500",
        "qtd_notas": "12",
        "energia_recuperada_media_kwh": "1000",
    }

    reasons = build_ranking_reasons(row)

    assert "classificado como risco alto pelo alvo proxy" in reasons
    assert "score operacional alto" in reasons
    assert "alto consumo faturado no período" in reasons
    assert "consumo médio por cliente ligado elevado" in reasons
    assert "percentual de clientes cortados elevado" in reasons
    assert "percentual de clientes baixados relevante" in reasons
    assert "presença de geração distribuída associada" in reasons
    assert "alto histórico de notas operacionais" in reasons
    assert "histórico de energia recuperada" in reasons


def test_ranking_explainer_generates_summary_and_csv(tmp_path: Path) -> None:
    dataset_path = tmp_path / "ml_transformer_dataset.csv"
    summary_path = tmp_path / "ml_explainability_summary.json"
    ranking_path = tmp_path / "ml_explainability_ranking.csv"

    _write_dataset(dataset_path)

    result = TransformerRankingExplainer(
        dataset_path=dataset_path,
        summary_path=summary_path,
        ranking_path=ranking_path,
    ).run()

    assert result.total_rows == 2
    assert result.explained_rows == 2
    assert summary_path.exists()
    assert ranking_path.exists()

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    ranking_rows = list(csv.DictReader(ranking_path.open("r", encoding="utf-8")))

    assert summary["total_rows"] == 2
    assert len(summary["top_10_transformers"]) == 2
    assert ranking_rows[0]["codigo_transformador"] == "A00001"
    assert "motivos_ranking" in ranking_rows[0]
    assert "alto consumo faturado no período" in ranking_rows[0]["motivos_ranking"]


def test_ranking_explainer_handles_missing_dataset(tmp_path: Path) -> None:
    dataset_path = tmp_path / "missing.csv"
    summary_path = tmp_path / "ml_explainability_summary.json"
    ranking_path = tmp_path / "ml_explainability_ranking.csv"

    result = TransformerRankingExplainer(
        dataset_path=dataset_path,
        summary_path=summary_path,
        ranking_path=ranking_path,
    ).run()

    assert result.total_rows == 0
    assert result.explained_rows == 0
    assert summary_path.exists()
    assert ranking_path.exists()

    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert summary["total_rows"] == 0
    assert summary["top_10_transformers"] == []


def _write_dataset(path: Path) -> None:
    rows = [
        {
            "codigo_transformador": "A00001",
            "codigo_subestacao": "SE",
            "codigo_alimentador": "AL",
            "mes_referencia": "2025-01",
            "risco_score": "80",
            "prioridade": "Alta",
            "target_risco_alto": "1",
            "consumo_faturado_kwh": "15000",
            "consumo_medio_por_cliente_ligado": "400",
            "qtd_ligado": "100",
            "qtd_cortado": "20",
            "qtd_baixado": "10",
            "percentual_cortado": "0.25",
            "percentual_baixado": "0.12",
            "energia_injetada_total": "500",
            "qtd_notas": "12",
            "energia_recuperada_media_kwh": "1000",
        },
        {
            "codigo_transformador": "A00002",
            "codigo_subestacao": "SE",
            "codigo_alimentador": "AL",
            "mes_referencia": "2025-01",
            "risco_score": "10",
            "prioridade": "Baixa",
            "target_risco_alto": "0",
            "consumo_faturado_kwh": "1000",
            "consumo_medio_por_cliente_ligado": "100",
            "qtd_ligado": "10",
            "qtd_cortado": "0",
            "qtd_baixado": "0",
            "percentual_cortado": "0",
            "percentual_baixado": "0",
            "energia_injetada_total": "0",
            "qtd_notas": "0",
            "energia_recuperada_media_kwh": "0",
        },
    ]

    fieldnames = [
        "codigo_transformador",
        "codigo_subestacao",
        "codigo_alimentador",
        "mes_referencia",
        "risco_score",
        "prioridade",
        "target_risco_alto",
        "consumo_faturado_kwh",
        "consumo_medio_por_cliente_ligado",
        "qtd_ligado",
        "qtd_cortado",
        "qtd_baixado",
        "percentual_cortado",
        "percentual_baixado",
        "energia_injetada_total",
        "qtd_notas",
        "energia_recuperada_media_kwh",
    ]

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
