import argparse

from src.aerial_housing_detection.reports.transformer_map_generator import (
    TransformerOperationalMapGenerator,
)
from src.aerial_housing_detection.services.grid_aggregation import (
    GridAggregationService,
)
from src.aerial_housing_detection.storage.loss_repository import LossRepository


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate transformer operational map.",
    )
    parser.add_argument(
        "--reference-month",
        required=True,
        help="Reference month in YYYY-MM format.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    loss_repository = LossRepository()
    loss_repository.initialize()

    records = loss_repository.list_monthly_loss_records(
        reference_month=args.reference_month,
    )
    coordinates_by_area = {
        str(record["area_id"]): (
            float(record["latitude"]),
            float(record["longitude"]),
        )
        for record in records
    }

    service = GridAggregationService(loss_repository=loss_repository)
    summaries = service.build_transformer_summaries(
        reference_month=args.reference_month,
    )

    generator = TransformerOperationalMapGenerator()
    output_path = generator.generate_html(
        summaries=summaries,
        coordinates_by_area=coordinates_by_area,
        reference_month=args.reference_month,
    )

    print(f"map_path={output_path}")


if __name__ == "__main__":
    main()
