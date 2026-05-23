from config.settings import get_settings
from src.aerial_housing_detection.domain.detection import RoofDetection


class DetectionPostProcessor:
    """Applies filtering and deduplication to roof detections."""

    def __init__(self) -> None:
        """Initialize post processor settings."""
        self.settings = get_settings()

    def process(self, detections: list[RoofDetection]) -> list[RoofDetection]:
        """Run post-processing over roof detections.

        Args:
            detections: Raw roof detections.

        Returns:
            Filtered and deduplicated detections.
        """
        filtered = self._filter_by_confidence_and_area(detections)
        return self._deduplicate(filtered)

    def _filter_by_confidence_and_area(
        self,
        detections: list[RoofDetection],
    ) -> list[RoofDetection]:
        """Filter detections by confidence and pixel area."""
        return [
            detection
            for detection in detections
            if detection.confidence_score >= self.settings.default_confidence_score
            and self.settings.min_roof_area_px <= detection.area_px <= self.settings.max_roof_area_px
        ]

    def _deduplicate(self, detections: list[RoofDetection]) -> list[RoofDetection]:
        """Remove duplicated detections using IoU."""
        if not detections:
            return []

        sorted_detections = sorted(
            detections,
            key=lambda detection: detection.confidence_score,
            reverse=True,
        )

        selected: list[RoofDetection] = []

        for detection in sorted_detections:
            overlaps_existing = any(detection.bbox.iou(existing.bbox) > 0.45 for existing in selected)

            if not overlaps_existing:
                selected.append(detection)

        return selected
