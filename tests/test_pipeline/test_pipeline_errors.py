from pathlib import Path

import pytest

from src.aerial_housing_detection.domain.exceptions import PipelineExecutionError
from src.aerial_housing_detection.pipeline.orchestrator import DetectionPipeline


def test_pipeline_raises_clean_error_for_missing_image(tmp_path: Path) -> None:
    pipeline = DetectionPipeline()
    missing_image = tmp_path / "missing.png"

    with pytest.raises(PipelineExecutionError, match="Image not found"):
        pipeline.run(missing_image)
