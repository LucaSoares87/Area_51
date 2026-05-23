from pathlib import Path

from src.aerial_housing_detection.domain.detection import (
    DetectionResult,
    DetectionStatus,
    ImageMetadata,
    RoofDetection,
)
from src.aerial_housing_detection.domain.geometry import BoundingBox, ImageSize
from src.aerial_housing_detection.reports.report_generator import ReportGenerator


def test_report_generator_creates_csv_file(tmp_path: Path) -> None:
    image_path = tmp_path / "area.png"
    image_path.write_bytes(b"fake")

    metadata = ImageMetadata(
        file_name="area.png",
        file_path=image_path,
        image_size=ImageSize(width=1024, height=768),
        file_size_bytes=4,
        extension=".png",
    )

    result = DetectionResult(
        analysis_id="analysis-test",
        status=DetectionStatus.COMPLETED,
        image_metadata=metadata,
        detections=[
            RoofDetection(
                bbox=BoundingBox(x=10, y=20, width=100, height=80),
                confidence_score=0.85,
            )
        ],
    )

    generator = ReportGenerator()
    report_path = generator.generate_csv(result)

    assert report_path.exists()
    assert report_path.suffix == ".csv"

    content = report_path.read_text(encoding="utf-8")
    assert "analysis-test" in content
    assert "estimated_residences" in content
    assert "0.85" in content
