from pathlib import Path

from PIL import Image

from config.settings import get_settings
from src.aerial_housing_detection.domain.detection import ImageMetadata
from src.aerial_housing_detection.domain.geometry import ImageSize


class ImagePreprocessor:
    """Validates and extracts metadata from aerial images."""

    def __init__(self) -> None:
        """Initialize image preprocessor settings."""
        self.settings = get_settings()

    def validate_image_path(self, image_path: Path) -> None:
        """Validate image path, extension and file size.

        Args:
            image_path: Path to the input image.

        Raises:
            FileNotFoundError: If the image does not exist.
            ValueError: If the image extension or size is invalid.
        """
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        if not image_path.is_file():
            raise ValueError(f"Path is not a file: {image_path}")

        extension = image_path.suffix.lower()
        if extension not in self.settings.allowed_image_extensions:
            raise ValueError(f"Unsupported image extension: {extension}")

        max_size_bytes = self.settings.max_image_size_mb * 1024 * 1024
        if image_path.stat().st_size > max_size_bytes:
            raise ValueError(f"Image exceeds maximum size of {self.settings.max_image_size_mb} MB")

    def extract_metadata(self, image_path: Path) -> ImageMetadata:
        """Extract metadata from an aerial image.

        Args:
            image_path: Path to the input image.

        Returns:
            Image metadata.
        """
        self.validate_image_path(image_path)

        with Image.open(image_path) as image:
            width, height = image.size

        return ImageMetadata(
            file_name=image_path.name,
            file_path=image_path,
            image_size=ImageSize(width=width, height=height),
            file_size_bytes=image_path.stat().st_size,
            extension=image_path.suffix.lower(),
        )

    def preprocess(self, image_path: Path) -> ImageMetadata:
        """Run the initial preprocessing stage.

        Args:
            image_path: Path to the input image.

        Returns:
            Image metadata prepared for the pipeline.
        """
        return self.extract_metadata(image_path)
