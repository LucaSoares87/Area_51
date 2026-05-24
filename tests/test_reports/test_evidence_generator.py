import json
from pathlib import Path

from src.aerial_housing_detection.domain.evidence import OperationalEvidence
from src.aerial_housing_detection.reports.evidence_generator import EvidenceGenerator


def test_evidence_generator_creates_json_file(tmp_path: Path) -> None:
    evidence = OperationalEvidence(
        analysis_id="analysis-test",
        image_path=Path("data/raw/test_area.png"),
        raw_detection_count=3,
        filtered_detection_count=2,
        final_detection_count=2,
        estimated_residences=2,
        average_confidence=0.8,
        status="completed",
        csv_report_path=Path("reports/analysis-test_report.csv"),
        html_map_path=Path("reports/analysis-test_map.html"),
    )

    generator = EvidenceGenerator(output_dir=tmp_path)
    output_path = generator.generate_json(evidence)

    assert output_path.exists()

    data = json.loads(output_path.read_text(encoding="utf-8"))

    assert data["analysis_id"] == "analysis-test"
    assert data["raw_detection_count"] == 3
    assert data["filtered_detection_count"] == 2
    assert data["final_detection_count"] == 2
    assert data["estimated_residences"] == 2
    assert data["average_confidence"] == 0.8
    assert data["status"] == "completed"
    assert data["csv_report_path"] == str(Path("reports/analysis-test_report.csv"))
    assert data["html_map_path"] == str(Path("reports/analysis-test_map.html"))
