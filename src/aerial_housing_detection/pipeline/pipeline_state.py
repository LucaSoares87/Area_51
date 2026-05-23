from dataclasses import dataclass, field
from pathlib import Path

from src.aerial_housing_detection.domain.detection import (
    DetectionResult,
    DetectionStatus,
    ImageMetadata,
    RoofDetection,
)
from src.aerial_housing_detection.domain.exceptions import PipelineExecutionError


@dataclass
class PipelineState:
    """Stores state during one aerial housing detection pipeline execution."""

    analysis_id: str
    image_path: Path
    status: DetectionStatus = DetectionStatus.CREATED
    image_metadata: ImageMetadata | None = None
    raw_detections: list[RoofDetection] = field(default_factory=list)
    final_detections: list[RoofDetection] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def mark_processing(self) -> None:
        """Mark pipeline execution as processing."""
        self.status = DetectionStatus.PROCESSING

    def mark_completed(self) -> None:
        """Mark pipeline execution as completed."""
        self.status = DetectionStatus.COMPLETED

    def mark_failed(self, error: str) -> None:
        """Mark pipeline execution as failed.

        Args:
            error: Error message.
        """
        self.status = DetectionStatus.FAILED
        self.errors.append(error)

    def require_metadata(self) -> ImageMetadata:
        """Return image metadata or raise an error if unavailable.

        Returns:
            Image metadata.

        Raises:
            PipelineExecutionError: If metadata was not produced.
        """
        if self.image_metadata is None:
            raise PipelineExecutionError("Pipeline image metadata is not available.")

        return self.image_metadata

    def to_detection_result(self) -> DetectionResult:
        """Convert pipeline state into detection result.

        Returns:
            Detection result.

        Raises:
            PipelineExecutionError: If metadata was not produced.
        """
        metadata = self.require_metadata()

        return DetectionResult(
            analysis_id=self.analysis_id,
            status=self.status,
            image_metadata=metadata,
            detections=self.final_detections,
            errors=self.errors,
        )
