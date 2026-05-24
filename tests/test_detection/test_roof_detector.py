from pathlib import Path

from src.aerial_housing_detection.detection.roof_detector import RoofDetector
from src.aerial_housing_detection.domain.detection import ImageMetadata
from src.aerial_housing_detection.domain.geometry import ImageSize


class MissingModelManager:
    def has_primary_detector(self) -> bool:
        return False

    def get_primary_detector_path(self) -> None:
        return None


class BrokenModelManager:
    def has_primary_detector(self) -> bool:
        return True

    def get_primary_detector_path(self) -> Path:
        return Path("models/yolo/missing.pt")


def build_metadata() -> ImageMetadata:
    return ImageMetadata(
        file_name="test_area.png",
        file_path=Path("data/raw/test_area.png"),
        file_size_bytes=1024,
        extension=".png",
        image_size=ImageSize(width=1024, height=768),
    )

def test_roof_detector_uses_deterministic_fallback_without_model() -> None:
    detector = RoofDetector(model_manager=MissingModelManager())

    detections = detector.detect(
        image_path=Path("data/raw/test_area.png"),
        metadata=build_metadata(),
    )

    assert len(detections) == 2
    assert all(detection.confidence_score > 0 for detection in detections)


def test_roof_detector_falls_back_when_model_detection_fails() -> None:
    detector = RoofDetector(model_manager=BrokenModelManager())

    detections = detector.detect(
        image_path=Path("data/raw/test_area.png"),
        metadata=build_metadata(),
    )

    assert len(detections) == 2
    assert all(detection.bbox.width > 0 for detection in detections)
