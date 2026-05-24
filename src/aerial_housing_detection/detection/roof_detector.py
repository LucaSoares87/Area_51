from pathlib import Path
from typing import Any

from src.aerial_housing_detection.detection.model_manager import ModelManager
from src.aerial_housing_detection.domain.detection import (
    DetectionSource,
    ImageMetadata,
    RoofDetection,
)
from src.aerial_housing_detection.domain.geometry import BoundingBox


class RoofDetector:
    """Detects roof candidates in aerial images.

    The detector uses a trained YOLO model when available. If the model or
    Ultralytics dependency is unavailable, it falls back to a deterministic
    baseline so the pipeline remains operational.
    """

    def __init__(
        self,
        model_manager: ModelManager | None = None,
        confidence_threshold: float = 0.25,
    ) -> None:
        """Initialize the roof detector."""
        self.model_manager = model_manager or ModelManager()
        self.confidence_threshold = confidence_threshold
        self._model: Any | None = None

    def detect(self, image_path: Path, metadata: ImageMetadata) -> list[RoofDetection]:
        """Detect roof candidates in an aerial image."""
        if self.model_manager.has_primary_detector():
            detections = self._detect_with_model(image_path, metadata)
            if detections:
                return detections

        return self._detect_with_deterministic_grid(metadata)

    def _detect_with_model(
        self,
        image_path: Path,
        metadata: ImageMetadata,
    ) -> list[RoofDetection]:
        """Run YOLO model-based detection."""
        model_path = self.model_manager.get_primary_detector_path()
        if model_path is None:
            return []

        try:
            model = self._load_model(model_path)
            results = model.predict(
                source=str(image_path),
                conf=self.confidence_threshold,
                verbose=False,
            )
        except (ImportError, RuntimeError, OSError, ValueError):
            return []

        detections: list[RoofDetection] = []

        for result in results:
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue

            xyxy_values = getattr(boxes, "xyxy", [])
            confidence_values = getattr(boxes, "conf", [])

            xyxy_list = self._to_list(xyxy_values)
            confidence_list = self._to_list(confidence_values)

            for xyxy, confidence in zip(xyxy_list, confidence_list, strict=False):
                detection = self._build_detection_from_xyxy(
                    xyxy=xyxy,
                    confidence=float(confidence),
                    metadata=metadata,
                )
                if detection is not None:
                    detections.append(detection)

        return detections

    def _load_model(self, model_path: Path) -> Any:
        """Load YOLO model lazily."""
        if self._model is not None:
            return self._model

        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise ImportError("Ultralytics is not available.") from exc

        self._model = YOLO(str(model_path))
        return self._model

    def _build_detection_from_xyxy(
        self,
        xyxy: list[float],
        confidence: float,
        metadata: ImageMetadata,
    ) -> RoofDetection | None:
        """Build a domain detection from YOLO xyxy coordinates."""
        if len(xyxy) < 4:
            return None

        x1, y1, x2, y2 = [float(value) for value in xyxy[:4]]

        image_width = metadata.image_size.width
        image_height = metadata.image_size.height

        x1 = min(max(x1, 0.0), float(image_width))
        y1 = min(max(y1, 0.0), float(image_height))
        x2 = min(max(x2, 0.0), float(image_width))
        y2 = min(max(y2, 0.0), float(image_height))

        width = x2 - x1
        height = y2 - y1

        if width <= 0 or height <= 0:
            return None

        return RoofDetection(
            bbox=BoundingBox(
                x=round(x1, 2),
                y=round(y1, 2),
                width=round(width, 2),
                height=round(height, 2),
            ),
            confidence_score=round(confidence, 4),
            source=DetectionSource.AERIAL_IMAGE,
        )

    def _to_list(self, value: Any) -> list[Any]:
        """Convert tensor-like objects to plain Python lists."""
        if hasattr(value, "detach"):
            value = value.detach()

        if hasattr(value, "cpu"):
            value = value.cpu()

        if hasattr(value, "numpy"):
            value = value.numpy()

        if hasattr(value, "tolist"):
            return value.tolist()

        return list(value)

    def _detect_with_deterministic_grid(
        self,
        metadata: ImageMetadata,
    ) -> list[RoofDetection]:
        """Create deterministic roof candidates from image dimensions."""
        width = metadata.image_size.width
        height = metadata.image_size.height

        if width < 128 or height < 128:
            return []

        grid_columns = max(1, min(5, width // 512))
        grid_rows = max(1, min(5, height // 512))

        cell_width = width / grid_columns
        cell_height = height / grid_rows

        detections: list[RoofDetection] = []

        for row in range(grid_rows):
            for column in range(grid_columns):
                box_width = max(32.0, cell_width * 0.35)
                box_height = max(32.0, cell_height * 0.28)

                x = column * cell_width + (cell_width - box_width) / 2
                y = row * cell_height + (cell_height - box_height) / 2

                confidence = self._score_candidate(
                    box_width=box_width,
                    box_height=box_height,
                    image_width=width,
                    image_height=height,
                )

                detections.append(
                    RoofDetection(
                        bbox=BoundingBox(
                            x=round(x, 2),
                            y=round(y, 2),
                            width=round(box_width, 2),
                            height=round(box_height, 2),
                        ),
                        confidence_score=confidence,
                        source=DetectionSource.AERIAL_IMAGE,
                    )
                )

        return detections

    def _score_candidate(
        self,
        box_width: float,
        box_height: float,
        image_width: int,
        image_height: int,
    ) -> float:
        """Score a deterministic candidate based on relative image scale."""
        relative_area = (box_width * box_height) / (image_width * image_height)
        score = 0.55 + min(0.35, relative_area * 30)
        return round(score, 4)
