import subprocess
import sys

from src.aerial_housing_detection.services.demo_realistic_analysis import (
    RealisticAnalysisRequest,
    RealisticDemoAnalysisService,
)


def test_realistic_analysis_returns_selected_transformer() -> None:
    subprocess.run(
        [sys.executable, "-m", "scripts.seed_realistic_demo_db"],
        check=True,
    )

    service = RealisticDemoAnalysisService()
    result = service.analyze(
        RealisticAnalysisRequest(latitude=-7.9401, longitude=-34.8734)
    )

    selected = result["selected_transformer"]

    assert selected["transformer_code"] == "TR-001"
    assert selected["feeder_code"] == "AL-01"
    assert selected["substation_code"] == "SE-01"
    assert selected["houses"]["cras"] == 127
    assert selected["houses"]["ibge"] == 102
    assert selected["houses"]["roof_image"] == 137
    assert selected["houses"]["average"] == 122
    assert selected["houses"]["estimated_range"] == {"min": 120, "max": 124}
    assert selected["energy"]["estimated_loss_kwh"] > 0


def test_realistic_analysis_exports_csv() -> None:
    subprocess.run(
        [sys.executable, "-m", "scripts.seed_realistic_demo_db"],
        check=True,
    )

    service = RealisticDemoAnalysisService()
    csv_content = service.export_csv(
        RealisticAnalysisRequest(latitude=-7.9401, longitude=-34.8734)
    )

    assert "transformer_code" in csv_content
    assert "TR-001" in csv_content
    assert "estimated_loss_kwh" in csv_content