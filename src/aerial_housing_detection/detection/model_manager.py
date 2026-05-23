from pathlib import Path

from config.settings import get_settings


class ModelManager:
    """Manages model paths and future model loading."""

    def __init__(self) -> None:
        """Initialize model manager settings."""
        self.settings = get_settings()

    def get_primary_detector_path(self) -> Path | None:
        """Return primary detector path when available.

        Returns:
            Path to the primary detector model or None.
        """
        candidates = (
            self.settings.models_dir / "roof_detector.pt",
            self.settings.models_dir / "best.pt",
        )

        for candidate in candidates:
            if candidate.exists():
                return candidate

        return None

    def has_primary_detector(self) -> bool:
        """Return whether a trained primary detector is available."""
        return self.get_primary_detector_path() is not None
