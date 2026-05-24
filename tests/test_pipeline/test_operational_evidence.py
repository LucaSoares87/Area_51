import json
from pathlib import Path

from src.aerial_housing_detection.pipeline.orchestrator import DetectionPipeline
from src.aerial_housing_detection.reports.evidence_generator import EvidenceGenerator


def test_pipeline_generates_operational_evidence(tmp_path: Path) -> None:
    image_path = tmp_path / "test_area.png"
    image_path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01"
        b"\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00"
        b"\x90wS\xde"
        b"\x00\x00\x00\x0cIDAT"
        b"\x08\xd7c\xf8\xff\xff?\x00"
        b"\x05\xfe\x02\xfeA\xe2'\xb5"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    pipeline = DetectionPipeline(
        evidence_generator=EvidenceGenerator(output_dir=tmp_path),
    )

    result = pipeline.run(image_path)

    assert result.roof_count >= 0
    assert pipeline.last_evidence_path is not None
    assert pipeline.last_evidence_path.exists()

    data = json.loads(pipeline.last_evidence_path.read_text(encoding="utf-8"))

    assert data["analysis_id"] == result.analysis_id
    assert data["final_detection_count"] == result.roof_count
    assert data["csv_report_path"] == str(result.csv_report_path)
    assert data["html_map_path"] == str(result.html_map_path)
