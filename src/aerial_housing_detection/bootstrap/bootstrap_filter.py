from src.aerial_housing_detection.domain.bootstrap import (
    BootstrapClassification,
    BootstrapLabel,
)
from src.aerial_housing_detection.domain.detection import RoofDetection


class BootstrapFilter:
    """Rule-based bootstrap filter for roof detections.

    This initial version creates a stable contract for the future classifier.
    It is intentionally conservative and can be replaced by a trained model.
    """

    def __init__(
        self,
        positive_threshold: float = 0.65,
        uncertain_threshold: float = 0.4,
    ) -> None:
        self.positive_threshold = positive_threshold
        self.uncertain_threshold = uncertain_threshold

    def classify(self, detection: RoofDetection) -> BootstrapClassification:
        score = detection.confidence_score

        if score >= self.positive_threshold:
            return BootstrapClassification(
                label=BootstrapLabel.POSITIVE,
                confidence_score=score,
                reason="confidence_above_positive_threshold",
            )

        if score >= self.uncertain_threshold:
            return BootstrapClassification(
                label=BootstrapLabel.UNCERTAIN,
                confidence_score=score,
                reason="confidence_between_thresholds",
            )

        return BootstrapClassification(
            label=BootstrapLabel.NEGATIVE,
            confidence_score=score,
            reason="confidence_below_uncertain_threshold",
        )

    def keep(self, detection: RoofDetection) -> bool:
        classification = self.classify(detection)
        return not classification.is_negative

    def filter(self, detections: list[RoofDetection]) -> list[RoofDetection]:
        return [detection for detection in detections if self.keep(detection)]
