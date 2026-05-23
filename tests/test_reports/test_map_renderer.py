from pathlib import Path

from src.aerial_housing_detection.domain.detection import (
    DetectionResult,
    DetectionStatus,
    ImageMetadata,
    RoofDetection,
)
from src.aerial_housing_detection.domain.geometry import BoundingBox, ImageSize
from src.aerial_housing_detection.reports.map_renderer import MapRenderer


def test_map_renderer_creates_html_file(tmp_path: Path) -> None:
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
        analysis_id="analysis-map-test",
        status=DetectionStatus.COMPLETED,
        image_metadata=metadata,
        detections=[
            RoofDetection(
                bbox=BoundingBox(x=10, y=20, width=100, height=80),
                confidence_score=0.82,
            )
        ],
    )

    renderer = MapRenderer()
    html_path = renderer.render_html(result)

    assert html_path.exists()
    assert html_path.suffix == ".html"

    content = html_path.read_text(encoding="utf-8")
    assert "Relatório de Detecção Aérea de Residências" in content
    assert "analysis-map-test" in content
    assert "Residências estimadas" in content
