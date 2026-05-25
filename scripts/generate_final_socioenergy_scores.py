import argparse

from src.aerial_housing_detection.services.final_socioenergy_score import (
    FinalSocioEnergyScoreService,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate final socioenergy scores.",
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

    service = FinalSocioEnergyScoreService()
    scores = service.build_scores(
        reference_month=args.reference_month,
        estimated_roofs_by_area=estimated_roofs_by_area,
    )

    print("final_socioenergy_scores")
    print(f"reference_month={args.reference_month}")
    print(f"total_records={len(scores)}")

    for position, score in enumerate(scores, start=1):
        print(
            f"{position}. "
            f"area_id={score.area_id} "
            f"transformer={score.transformer_code} "
            f"feeder={score.feeder} "
            f"adjusted_loss_kwh={score.adjusted_loss_kwh} "
            f"solar_offset_ratio={score.solar_offset_ratio} "
            f"final_priority_score={score.final_priority_score} "
            f"risk={score.final_risk_level}"
        )


if __name__ == "__main__":
    main()
