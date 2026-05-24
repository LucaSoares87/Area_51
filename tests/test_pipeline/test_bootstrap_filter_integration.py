from pathlib import Path

from src.aerial_housing_detection.domain.detection import DetectionSource, RoofDetection
from src.aerial_housing_detection.domain.geometry import BoundingBox
from src.aerial_housing_detection.pipeline.orchestrator import DetectionPipeline


class FixedRoofDetector:
    def detect(self, image_path: Path, metadata: object) -> list[RoofDetection]:
        return [
            RoofDetection(
                bbox=BoundingBox(x=10, y=10, width=100, height=80),
                confidence_score=0.9,
                source=DetectionSource.AERIAL_IMAGE,
            ),
            RoofDetection(
                bbox=BoundingBox(x=120, y=10, width=100, height=80),
                confidence_score=0.7,
                source=DetectionSource.AERIAL_IMAGE,
            ),
            RoofDetection(
                bbox=BoundingBox(x=230, y=10, width=100, height=80),
                confidence_score=0.2,
                source=DetectionSource.AERIAL_IMAGE,
            ),
        ]


def test_pipeline_applies_bootstrap_filter_before_final_count(tmp_path: Path) -> None:
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

    pipeline = DetectionPipeline(roof_detector=FixedRoofDetector())

    result = pipeline.run_detection(image_path)

    assert result.roof_count == 2
    assert result.estimated_residences == 2
    assert result.average_confidence > 0
