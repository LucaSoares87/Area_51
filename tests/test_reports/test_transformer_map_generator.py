from pathlib import Path

from src.aerial_housing_detection.domain.grid_aggregation import (
    TransformerLossSummary,
)
from src.aerial_housing_detection.reports.transformer_map_generator import (
    TransformerOperationalMapGenerator,
)


def test_transformer_operational_map_generator_creates_html_file(
    tmp_path: Path,
) -> None:
    summary = TransformerLossSummary(
        area_id="area-001",
        transformer_code="TR-001",
        feeder="AL-01",
        reference_month="2026-05",
        customer_count=120,
        estimated_loss_kwh=3700.0,
        estimated_generation_kwh=950.0,
        adjusted_loss_kwh=2750.0,
        estimated_loss_percent=0.308333,
        solar_offset_ratio=0.256757,
        priority_score=83.5,
        risk_level="high",
    )

    generator = TransformerOperationalMapGenerator(output_dir=tmp_path)
    output_path = generator.generate_html(
        summaries=[summary],
        coordinates_by_area={
            "area-001": (-7.9401, -34.8734),
        },
        reference_month="2026-05",
    )

    content = output_path.read_text(encoding="utf-8")

    assert output_path.exists()
    assert output_path.name == "transformer_operational_map.html"
    assert "Mapa Operacional de Transformadores" in content
    assert "TR-001" in content
    assert "AL-01" in content
    assert "area-001" in content
