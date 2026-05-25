from pathlib import Path

from src.aerial_housing_detection.domain.socioenergy import SocioEnergyIndicator
from src.aerial_housing_detection.reports.socioenergy_dashboard_generator import (
    SocioEnergyDashboardGenerator,
)


def test_socioenergy_dashboard_generator_creates_html_file(
    tmp_path: Path,
) -> None:
    indicator = SocioEnergyIndicator(
        area_id="area-001",
        reference_month="2026-05",
        sector_id="sector-001",
        territory_id="cras-territory-001",
        population=480,
        households=120,
        estimated_roofs=145,
        customer_count=120,
        roof_customer_gap=25,
        household_customer_gap=0,
        assisted_families=80,
        vulnerable_families=50,
        vulnerability_ratio=0.625,
        estimated_loss_kwh=3700.0,
        estimated_loss_percent=0.308333,
        operational_risk_level="high",
        operational_priority_score=83.5,
        socioenergy_priority_score=58.5417,
    )

    generator = SocioEnergyDashboardGenerator(output_dir=tmp_path)

    output_path = generator.generate_html(
        indicators=[indicator],
        reference_month="2026-05",
    )

    content = output_path.read_text(encoding="utf-8")

    assert output_path.exists()
    assert output_path.name == "socioenergy_dashboard.html"
    assert "Visão Socioenergética" in content
    assert "Ranking socioenergético" in content
    assert "area-001" in content
    assert "sector-001" in content
    assert "cras-territory-001" in content
