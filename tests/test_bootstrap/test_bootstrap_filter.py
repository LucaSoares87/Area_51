from src.aerial_housing_detection.bootstrap.bootstrap_filter import BootstrapFilter
from src.aerial_housing_detection.domain.bootstrap import BootstrapLabel
from src.aerial_housing_detection.domain.detection import DetectionSource, RoofDetection
from src.aerial_housing_detection.domain.geometry import BoundingBox


def build_detection(confidence_score: float) -> RoofDetection:
    return RoofDetection(
        bbox=BoundingBox(x=10, y=10, width=100, height=80),
        confidence_score=confidence_score,
        source=DetectionSource.AERIAL_IMAGE,
    )


def test_bootstrap_filter_classifies_positive_detection() -> None:
    bootstrap_filter = BootstrapFilter()

    result = bootstrap_filter.classify(build_detection(0.9))

    assert result.label == BootstrapLabel.POSITIVE
    assert result.is_positive


def test_bootstrap_filter_classifies_uncertain_detection() -> None:
    bootstrap_filter = BootstrapFilter()

    result = bootstrap_filter.classify(build_detection(0.5))

    assert result.label == BootstrapLabel.UNCERTAIN
    assert result.is_uncertain


def test_bootstrap_filter_classifies_negative_detection() -> None:
    bootstrap_filter = BootstrapFilter()

    result = bootstrap_filter.classify(build_detection(0.2))

    assert result.label == BootstrapLabel.NEGATIVE
    assert result.is_negative


def test_bootstrap_filter_removes_negative_detections() -> None:
    bootstrap_filter = BootstrapFilter()

    detections = [
        build_detection(0.9),
        build_detection(0.5),
        build_detection(0.2),
    ]

    filtered = bootstrap_filter.filter(detections)

    assert len(filtered) == 2
    assert all(detection.confidence_score >= 0.4 for detection in filtered)
