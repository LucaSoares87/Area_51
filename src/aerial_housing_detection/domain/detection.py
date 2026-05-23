from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from uuid import uuid4

from src.aerial_housing_detection.domain.geometry import BoundingBox, ImageSize


class DetectionSource(str, Enum):
    """Available sources for roof detections."""

    AERIAL_IMAGE = "aerial_image"
    MANUAL_REVIEW = "manual_review"
    EXTERNAL_SOURCE = "external_source"


class DetectionStatus(str, Enum):
    """Lifecycle status for a detection result."""

    CREATED = "created"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class ImageMetadata:
    """Metadata extracted from an input aerial image."""

    file_name: str
    file_path: Path
    image_size: ImageSize
    file_size_bytes: int
    extension: str

    @property
    def file_size_mb(self) -> float:
        """Return image file size in megabytes."""
        return self.file_size_bytes / (1024 * 1024)

    def to_dict(self) -> dict[str, object]:
        """Return serializable image metadata."""
        return {
            "file_name": self.file_name,
            "file_path": str(self.file_path),
            "width": self.image_size.width,
            "height": self.image_size.height,
            "total_pixels": self.image_size.total_pixels,
            "file_size_bytes": self.file_size_bytes,
            "file_size_mb": round(self.file_size_mb, 4),
            "extension": self.extension,
        }


@dataclass(frozen=True)
class RoofDetection:
    """Represents a detected roof candidate."""

    bbox: BoundingBox
    confidence_score: float
    source: DetectionSource = DetectionSource.AERIAL_IMAGE
    detection_id: str = field(default_factory=lambda: uuid4().hex)

    def __post_init__(self) -> None:
        """Validate detection confidence."""
        if not 0 <= self.confidence_score <= 1:
            raise ValueError("Confidence score must be between 0 and 1.")

    @property
    def area_px(self) -> float:
        """Return roof candidate area in pixels."""
        return self.bbox.area

    def to_dict(self) -> dict[str, object]:
        """Return serializable roof detection data."""
        return {
            "detection_id": self.detection_id,
            "bbox": self.bbox.to_dict(),
            "confidence_score": self.confidence_score,
            "source": self.source.value,
            "area_px": self.area_px,
        }


@dataclass
class DetectionResult:
    """Represents the final result of a roof detection process."""

    analysis_id: str
    status: DetectionStatus
    image_metadata: ImageMetadata
    detections: list[RoofDetection] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def roof_count(self) -> int:
        """Return total roof detections."""
        return len(self.detections)

    @property
    def estimated_residences(self) -> int:
        """Return estimated housing unit count."""
        return self.roof_count

    @property
    def average_confidence(self) -> float:
        """Return average confidence score."""
        if not self.detections:
            return 0.0

        score = sum(detection.confidence_score for detection in self.detections)
        return round(score / len(self.detections), 4)

    def to_dict(self) -> dict[str, object]:
        """Return serializable detection result."""
        return {
            "analysis_id": self.analysis_id,
            "status": self.status.value,
            "image_metadata": self.image_metadata.to_dict(),
            "roof_count": self.roof_count,
            "estimated_residences": self.estimated_residences,
            "average_confidence": self.average_confidence,
            "detections": [detection.to_dict() for detection in self.detections],
            "errors": self.errors,
            "created_at": self.created_at.isoformat(),
        }
