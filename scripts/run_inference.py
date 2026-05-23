import argparse
from pathlib import Path

from src.aerial_housing_detection.domain.exceptions import AerialHousingDetectionError
from src.aerial_housing_detection.pipeline.orchestrator import DetectionPipeline


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run aerial housing detection for a local image."
    )
    parser.add_argument(
        "--image",
        required=True,
        help="Path to the input aerial image.",
    )
    return parser.parse_args()


def main() -> None:
    """Run inference and print output paths."""
    args = parse_args()
    image_path = Path(args.image)

    try:
        pipeline = DetectionPipeline()
        result = pipeline.run(image_path)
    except AerialHousingDetectionError as exc:
        print(f"error={exc}")
        raise SystemExit(1) from exc

    print(f"analysis_id={result.analysis_id}")
    print(f"estimated_residences={result.estimated_residences}")
    print(f"roof_count={result.roof_count}")
    print(f"confidence_score={result.confidence_score}")
    print(f"csv_report_path={result.csv_report_path}")
    print(f"html_map_path={result.html_map_path}")


if __name__ == "__main__":
    main()
