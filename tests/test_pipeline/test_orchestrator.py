from pathlib import Path

from PIL import Image

from src.aerial_housing_detection.pipeline.orchestrator import DetectionPipeline


def create_test_image(path: Path, size: tuple[int, int] = (1024, 768)) -> Path:
    image = Image.new("RGB", size, color="white")
    image.save(path)
    return path


def test_pipeline_runs_and_generates_outputs(tmp_path: Path) -> None:
    image_path = create_test_image(tmp_path / "area_teste.png")

    pipeline = DetectionPipeline()
    result = pipeline.run(image_path)

    assert result.analysis_id
    assert result.roof_count >= 1
    assert result.estimated_residences == result.roof_count
    assert 0 <= result.confidence_score <= 1
    assert result.csv_report_path.exists()
    assert result.html_map_path.exists()
