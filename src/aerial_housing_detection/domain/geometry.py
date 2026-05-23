from dataclasses import dataclass


@dataclass(frozen=True)
class BoundingBox:
    """Represents a rectangular detection area in image coordinates."""

    x: float
    y: float
    width: float
    height: float

    def __post_init__(self) -> None:
        """Validate bounding box dimensions."""
        if self.width <= 0:
            raise ValueError("Bounding box width must be greater than zero.")
        if self.height <= 0:
            raise ValueError("Bounding box height must be greater than zero.")
        if self.x < 0 or self.y < 0:
            raise ValueError("Bounding box coordinates cannot be negative.")

    @property
    def x_min(self) -> float:
        """Return minimum x coordinate."""
        return self.x

    @property
    def y_min(self) -> float:
        """Return minimum y coordinate."""
        return self.y

    @property
    def x_max(self) -> float:
        """Return maximum x coordinate."""
        return self.x + self.width

    @property
    def y_max(self) -> float:
        """Return maximum y coordinate."""
        return self.y + self.height

    @property
    def area(self) -> float:
        """Return bounding box area."""
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        """Return bounding box center point."""
        return (self.x + self.width / 2, self.y + self.height / 2)

    def intersects(self, other: "BoundingBox") -> bool:
        """Return whether this bounding box intersects another.

        Args:
            other: Another bounding box.

        Returns:
            True when both boxes intersect.
        """
        return not (
            self.x_max <= other.x_min
            or self.x_min >= other.x_max
            or self.y_max <= other.y_min
            or self.y_min >= other.y_max
        )

    def intersection_area(self, other: "BoundingBox") -> float:
        """Return intersection area with another bounding box.

        Args:
            other: Another bounding box.

        Returns:
            Intersection area in pixels.
        """
        if not self.intersects(other):
            return 0.0

        x_left = max(self.x_min, other.x_min)
        y_top = max(self.y_min, other.y_min)
        x_right = min(self.x_max, other.x_max)
        y_bottom = min(self.y_max, other.y_max)

        return max(0.0, x_right - x_left) * max(0.0, y_bottom - y_top)

    def iou(self, other: "BoundingBox") -> float:
        """Return intersection over union score.

        Args:
            other: Another bounding box.

        Returns:
            IoU score between 0 and 1.
        """
        intersection = self.intersection_area(other)
        if intersection == 0:
            return 0.0

        union = self.area + other.area - intersection
        if union <= 0:
            return 0.0

        return intersection / union

    def to_dict(self) -> dict[str, float]:
        """Return serializable bounding box data."""
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "area": self.area,
        }


@dataclass(frozen=True)
class GeoPoint:
    """Represents a geographic coordinate in WGS84."""

    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        """Validate geographic coordinate range."""
        if not -90 <= self.latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90.")
        if not -180 <= self.longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180.")

    def to_dict(self) -> dict[str, float]:
        """Return serializable geographic coordinate."""
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
        }


@dataclass(frozen=True)
class ImageSize:
    """Represents image dimensions in pixels."""

    width: int
    height: int

    def __post_init__(self) -> None:
        """Validate image dimensions."""
        if self.width <= 0:
            raise ValueError("Image width must be greater than zero.")
        if self.height <= 0:
            raise ValueError("Image height must be greater than zero.")

    @property
    def total_pixels(self) -> int:
        """Return total pixel count."""
        return self.width * self.height

    def to_dict(self) -> dict[str, int]:
        """Return serializable image size."""
        return {
            "width": self.width,
            "height": self.height,
            "total_pixels": self.total_pixels,
        }
