import argparse

from src.aerial_housing_detection.reports.socioenergy_dashboard_generator import (
    SocioEnergyDashboardGenerator,
)
from src.aerial_housing_detection.services.socioenergy_analysis import (
    SocioEnergyAnalysisService,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate socioenergy dashboard.",
    )
    parser.add_argument(
        "--reference-month",
        required=True,
        help="Reference month in YYYY-MM format.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    estimated_roofs_by_area = {
        "area-001": 145,
        "area-002": 110,
        "area-003": 175,
    }

    service = SocioEnergyAnalysisService()
    indicators = service.build_indicators(
        reference_month=args.reference_month,
        estimated_roofs_by_area=estimated_roofs_by_area,
    )

    generator = SocioEnergyDashboardGenerator()
    dashboard_path = generator.generate_html(
        indicators=indicators,
        reference_month=args.reference_month,
    )

    print(f"dashboard_path={dashboard_path}")


if __name__ == "__main__":
    main()
