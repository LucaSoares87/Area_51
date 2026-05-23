from pathlib import Path

from src.aerial_housing_detection.detection.model_manager import ModelManager
from src.aerial_housing_detection.domain.detection import (
    DetectionSource,
    ImageMetadata,
    RoofDetection,
)
from src.aerial_housing_detection.domain.geometry import BoundingBox


class RoofDetector:
    """Detects roof candidates in aerial images.

    This initial implementation is deterministic and model-ready. It avoids
    random outputs and provides a stable baseline until a trained detector is
    available.
    """

    def __init__(self, model_manager: ModelManager | None = None) -> None:
        """Initialize the roof detector.

        Args:
            model_manager: Optional model manager instance.
        """
        self.model_manager = model_manager or ModelManager()

    def detect(self, image_path: Path, metadata: ImageMetadata) -> list[RoofDetection]:
        """Detect roof candidates in an aerial image.

        Args:
            image_path: Path to the input image.
            metadata: Image metadata.

        Returns:
            List of roof detections.
        """
        if self.model_manager.has_primary_detector():
            return self._detect_with_model(image_path, metadata)

        return self._detect_with_deterministic_grid(metadata)

    def _detect_with_model(
        self,
        image_path: Path,
        metadata: ImageMetadata,
    ) -> list[RoofDetection]:
        """Run future model-based detection.

        Args:
            image_path: Path to the input image.
            metadata: Image metadata.

        Returns:
            List of roof detections.

        Raises:
            NotImplementedError: Until the trained detector is added.
        """
        raise NotImplementedError("Model-based roof detection will be implemented in the machine learning phase.")

    def _detect_with_deterministic_grid(
        self,
        metadata: ImageMetadata,
    ) -> list[RoofDetection]:
        """Create deterministic roof candidates from image dimensions.

        Args:
            metadata: Image metadata.

        Returns:
            List of stable roof candidate detections.
        """
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
        """Score a deterministic candidate based on relative image scale.

        Args:
            box_width: Candidate width.
            box_height: Candidate height.
            image_width: Image width.
            image_height: Image height.

        Returns:
            Confidence score between 0 and 1.
        """
        relative_area = (box_width * box_height) / (image_width * image_height)
        score = 0.55 + min(0.35, relative_area * 30)
        return round(score, 4)
