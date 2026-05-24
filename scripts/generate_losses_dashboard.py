import argparse

from src.aerial_housing_detection.reports.loss_dashboard_generator import (
    LossDashboardGenerator,
)
from src.aerial_housing_detection.storage.loss_repository import LossRepository


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate operational losses dashboard.",
    )
    parser.add_argument(
        "--reference-month",
        default="2026-05",
        help="Reference month in YYYY-MM format.",
    )
    return parser.parse_args()


def build_summary(records: list[dict[str, object]], reference_month: str) -> dict[str, object]:
    total_areas = len(records)
    critical_areas = sum(1 for record in records if record["risk_level"] == "critical")
    high_risk_areas = sum(1 for record in records if record["risk_level"] == "high")
    estimated_loss_kwh = sum(float(record["estimated_loss_kwh"]) for record in records)

    if records:
        average_loss_percent = sum(
            float(record["estimated_loss_percent"]) for record in records
        ) / len(records)
        top_priority_score = max(float(record["priority_score"]) for record in records)
    else:
        average_loss_percent = 0.0
        top_priority_score = 0.0

    return {
        "reference_month": reference_month,
        "total_areas": total_areas,
        "critical_areas": critical_areas,
        "high_risk_areas": high_risk_areas,
        "estimated_loss_kwh": estimated_loss_kwh,
        "average_loss_percent": average_loss_percent,
        "top_priority_score": top_priority_score,
    }


def main() -> None:
    args = parse_args()

    repository = LossRepository()
    repository.initialize()

    records = repository.list_monthly_loss_records(
        reference_month=args.reference_month,
    )
    summary = build_summary(records, args.reference_month)

    generator = LossDashboardGenerator()
    output_path = generator.generate_html(
        records=records,
        summary=summary,
        reference_month=args.reference_month,
    )

    print(f"dashboard_path={output_path}")


if __name__ == "__main__":
    main()
