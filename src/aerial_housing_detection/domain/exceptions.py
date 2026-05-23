class AerialHousingDetectionError(Exception):
    """Base exception for aerial housing detection errors."""


class ImageValidationError(AerialHousingDetectionError):
    """Raised when an input image is invalid."""


class PipelineExecutionError(AerialHousingDetectionError):
    """Raised when the pipeline cannot complete execution."""
