from pathlib import Path

from src.aerial_housing_detection.reports.loss_dashboard_generator import (
    LossDashboardGenerator,
)


def test_loss_dashboard_generator_creates_html_file(tmp_path: Path) -> None:
    records = [
        {
            "area_id": "area-001",
            "transformer_code": "TR-001",
            "latitude": -7.9401,
            "longitude": -34.8734,
            "neighborhood": "Maranguape I",
            "city": "Paulista",
            "feeder": "AL-01",
            "customer_count": 120,
            "reference_month": "2026-05",
            "injected_energy_kwh": 12000.0,
            "billed_consumption_kwh": 8300.0,
            "estimated_loss_kwh": 3700.0,
            "estimated_loss_percent": 0.308333,
            "risk_level": "high",
            "priority_score": 67.0,
        }
    ]
    summary = {
        "reference_month": "2026-05",
        "total_areas": 1,
        "critical_areas": 0,
        "high_risk_areas": 1,
        "estimated_loss_kwh": 3700.0,
        "average_loss_percent": 0.308333,
        "top_priority_score": 67.0,
    }

    generator = LossDashboardGenerator(output_dir=tmp_path)
    output_path = generator.generate_html(
        records=records,
        summary=summary,
        reference_month="2026-05",
    )

    assert output_path.exists()

    html = output_path.read_text(encoding="utf-8")

    assert "Visão Operacional de Perdas" in html
    assert "TR-001" in html
    assert "Maranguape I" in html
