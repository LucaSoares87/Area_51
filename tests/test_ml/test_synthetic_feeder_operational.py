import json
import sqlite3
from pathlib import Path

from src.aerial_housing_detection.ml.synthetic_feeder_operational import (
    SyntheticFeederOperationalBuilder,
    build_operational_summary,
    build_reclosers,
    build_route_points,
    build_section_rows,
    build_synthetic_feeder_dataset,
    build_transformers,
    calculate_loss_percentual,
    classify_heat_level,
)


def test_build_synthetic_feeder_dataset_returns_coherent_structure() -> None:
    dataset = build_synthetic_feeder_dataset()

    assert len(dataset["substations"]) == 1
    assert len(dataset["feeders"]) == 1
    assert len(dataset["route_points"]) == 11
    assert len(dataset["reclosers"]) == 3
    assert len(dataset["mv_customers"]) == 9
    assert len(dataset["transformers"]) == 60

    feeder = dataset["feeders"][0]

    assert feeder["codigo_subestacao"] == "HPO"
    assert feeder["codigo_alimentador"] == "HPO-0IL4"
    assert feeder["extensao_rede_km"] == 6.0
    assert feeder["total_uc_mt"] == 9
    assert feeder["total_transformadores"] == 60
    assert feeder["total_religadores"] == 3
    assert feeder["total_uc_bt"] > 0
    assert feeder["total_gd"] > 0
    assert feeder["consumo_gwh"] > 0
    assert feeder["energia_injetada_gwh"] > 0
    assert feeder["perda_estimada_gwh"] > 0
    assert feeder["perda_percentual"] > 0


def test_build_route_points_preserves_feeder_path_sequence() -> None:
    route_points = build_route_points("HPO-0IL4")

    assert len(route_points) == 11
    assert route_points[0]["tipo_ponto"] == "subestacao"
    assert route_points[0]["descricao"] == "Saída da Subestação HPO"
    assert route_points[-1]["descricao"] == "Fim do circuito principal"
    assert [row["sequencia"] for row in route_points] == list(range(1, 12))


def test_build_transformers_generates_operational_heatmap_inputs() -> None:
    transformers = build_transformers("HPO", "HPO-0IL4")

    assert len(transformers) == 60

    first = transformers[0]

    assert first["codigo_transformador"] == "TRF-HPO-0IL4-001"
    assert first["codigo_subestacao"] == "HPO"
    assert first["codigo_alimentador"] == "HPO-0IL4"
    assert first["trecho"] == "S01"
    assert first["uc_bt"] > 0
    assert first["consumo_mensal_mwh"] > 0
    assert first["perda_estimada_mwh"] > 0
    assert first["nivel_calor"] in {"BAIXO", "MEDIO", "ALTO"}


def test_build_reclosers_aggregates_downstream_network() -> None:
    transformers = build_transformers("HPO", "HPO-0IL4")
    reclosers = build_reclosers("HPO", "HPO-0IL4", transformers)

    assert len(reclosers) == 3

    first = reclosers[0]
    last = reclosers[-1]

    assert first["codigo_religador"] == "RLG-01"
    assert first["transformadores_jusante"] > last["transformadores_jusante"]
    assert first["uc_bt_jusante"] >= last["uc_bt_jusante"]
    assert first["perda_jusante_gwh"] >= last["perda_jusante_gwh"]
    assert first["nivel_calor"] in {"BAIXO", "MEDIO", "ALTO"}


def test_build_section_rows_groups_transformers_by_feeder_sections() -> None:
    dataset = build_synthetic_feeder_dataset()
    sections = build_section_rows(dataset)

    assert len(sections) == 4
    assert sum(row["transformadores"] for row in sections) == 60
    assert sum(row["uc_mt"] for row in sections) == 9
    assert all(row["distancia_km"] > 0 for row in sections)
    assert all(row["perda_estimada_gwh"] > 0 for row in sections)
    assert all(row["nivel_calor"] in {"BAIXO", "MEDIO", "ALTO"} for row in sections)


def test_build_operational_summary_contains_dashboard_indicators() -> None:
    dataset = build_synthetic_feeder_dataset()
    summary = build_operational_summary(dataset)

    assert summary["codigo_subestacao"] == "HPO"
    assert summary["codigo_alimentador"] == "HPO-0IL4"
    assert summary["extensao_rede_km"] == 6.0
    assert summary["total_uc_mt"] == 9
    assert summary["total_transformadores"] == 60
    assert summary["total_religadores"] == 3
    assert summary["total_uc_bt"] > 0
    assert summary["total_gd"] > 0
    assert summary["perda_estimada_gwh"] > 0
    assert summary["perda_percentual"] > 0
    assert len(summary["sections"]) == 4
    assert len(summary["reclosers"]) == 3


def test_loss_percentual_and_heat_level_rules() -> None:
    assert calculate_loss_percentual(2.0, 10.0) == 0.2
    assert calculate_loss_percentual(2.0, 0.0) == 0.0

    assert classify_heat_level(0.18, 30) == "ALTO"
    assert classify_heat_level(0.10, 30) == "MEDIO"
    assert classify_heat_level(0.04, 20) == "BAIXO"
    assert classify_heat_level(0.04, 100) == "ALTO"


def test_synthetic_feeder_operational_builder_generates_database_and_reports(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "area51.db"
    summary_path = tmp_path / "summary.json"
    route_path = tmp_path / "route.csv"
    sections_path = tmp_path / "sections.csv"

    result = SyntheticFeederOperationalBuilder(
        db_path=db_path,
        summary_path=summary_path,
        route_path=route_path,
        sections_path=sections_path,
    ).run()

    assert result.substations == 1
    assert result.feeders == 1
    assert result.route_points == 11
    assert result.reclosers == 3
    assert result.mv_customers == 9
    assert result.transformers == 60
    assert result.sections == 4

    assert db_path.exists()
    assert summary_path.exists()
    assert route_path.exists()
    assert sections_path.exists()

    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert summary["codigo_subestacao"] == "HPO"
    assert summary["codigo_alimentador"] == "HPO-0IL4"
    assert summary["total_transformadores"] == 60
    assert summary["total_religadores"] == 3
    assert len(summary["sections"]) == 4

    with sqlite3.connect(db_path) as connection:
        table_counts = {
            "substations": _count(connection, "synthetic_feeder_substations"),
            "feeders": _count(connection, "synthetic_feeder_feeders"),
            "route_points": _count(connection, "synthetic_feeder_route_points"),
            "reclosers": _count(connection, "synthetic_feeder_reclosers"),
            "mv_customers": _count(connection, "synthetic_feeder_mv_customers"),
            "transformers": _count(connection, "synthetic_feeder_transformers"),
            "sections": _count(connection, "synthetic_feeder_sections"),
        }

    assert table_counts == {
        "substations": 1,
        "feeders": 1,
        "route_points": 11,
        "reclosers": 3,
        "mv_customers": 9,
        "transformers": 60,
        "sections": 4,
    }


def test_synthetic_feeder_operational_builder_replaces_previous_rows(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "area51.db"
    summary_path = tmp_path / "summary.json"
    route_path = tmp_path / "route.csv"
    sections_path = tmp_path / "sections.csv"

    builder = SyntheticFeederOperationalBuilder(
        db_path=db_path,
        summary_path=summary_path,
        route_path=route_path,
        sections_path=sections_path,
    )

    builder.run()
    builder.run()

    with sqlite3.connect(db_path) as connection:
        assert _count(connection, "synthetic_feeder_substations") == 1
        assert _count(connection, "synthetic_feeder_feeders") == 1
        assert _count(connection, "synthetic_feeder_route_points") == 11
        assert _count(connection, "synthetic_feeder_reclosers") == 3
        assert _count(connection, "synthetic_feeder_mv_customers") == 9
        assert _count(connection, "synthetic_feeder_transformers") == 60
        assert _count(connection, "synthetic_feeder_sections") == 4


def _count(connection: sqlite3.Connection, table_name: str) -> int:
    return int(connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])
