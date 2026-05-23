import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.aerial_housing_detection.pipeline.orchestrator import DetectionPipeline


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate CSV and HTML reports for a local aerial image."
    )
    parser.add_argument(
        "--image",
        required=True,
        help="Path to the input aerial image.",
    )
    return parser.parse_args()


def main() -> None:
    """Generate reports and print output paths."""
    args = parse_args()
    image_path = Path(args.image)

    pipeline = DetectionPipeline()
    result = pipeline.run(image_path)

    print(f"CSV report generated at: {result.csv_report_path}")
    print(f"HTML map generated at: {result.html_map_path}")


if __name__ == "__main__":
    main()