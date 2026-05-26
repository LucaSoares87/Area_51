from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from PIL import Image

from config.settings import get_settings
from src.aerial_housing_detection.detection.roof_detector import RoofDetector
from src.aerial_housing_detection.domain.detection import ImageMetadata, ImageSize


@dataclass(frozen=True)
class RoofUploadResult:
    analysis_id: str
    filename: str
    content_type: str
    estimated_roofs: int
    confidence_score: float
    status: str


class RoofUploadService:
    def __init__(
        self,
        upload_dir: Path | None = None,
        detector: RoofDetector | None = None,
    ) -> None:
        settings = get_settings()
        self.upload_dir = upload_dir or settings.reports_dir / "uploads"
        self.detector = detector or RoofDetector()

    def analyze_upload(
        self,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> RoofUploadResult:
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        analysis_id = uuid4().hex
        safe_filename = self._safe_filename(filename)
        image_path = self.upload_dir / f"{analysis_id}_{safe_filename}"
        image_path.write_bytes(content)

        metadata = self._build_metadata(
            image_path=image_path,
            original_filename=safe_filename,
        )
        detections = self.detector.detect(image_path, metadata)

        return RoofUploadResult(
            analysis_id=analysis_id,
            filename=safe_filename,
            content_type=content_type,
            estimated_roofs=len(detections),
            confidence_score=self._average_confidence(detections),
            status="completed",
        )

    def _build_metadata(
        self,
        image_path: Path,
        original_filename: str,
    ) -> ImageMetadata:
        with Image.open(image_path) as image:
            width, height = image.size

        return ImageMetadata(
            file_name=original_filename,
            file_path=image_path,
            image_size=ImageSize(
                width=width,
                height=height,
            ),
            file_size_bytes=image_path.stat().st_size,
            extension=image_path.suffix.lower().lstrip("."),
        )

    def _safe_filename(self, filename: str) -> str:
        normalized = Path(filename).name.strip()

        if not normalized:
            return "uploaded_image.png"

        return normalized.replace(" ", "_")

    def _average_confidence(self, detections: list[object]) -> float:
        if not detections:
            return 0.0

        confidences = [
            float(getattr(detection, "confidence_score", 0.0))
            for detection in detections
        ]

        return round(sum(confidences) / len(confidences), 6)
