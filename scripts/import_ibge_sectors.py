import argparse
from pathlib import Path

from src.aerial_housing_detection.imports.ibge_importer import IbgeCsvImporter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import aggregated IBGE census sectors from CSV.",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="CSV file path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    importer = IbgeCsvImporter()
    result = importer.import_csv(Path(args.input))

    print("ibge_sector_import")
    print(f"input_path={result.input_path}")
    print(f"imported_rows={result.imported_rows}")
    print(f"skipped_rows={result.skipped_rows}")
    print(f"success={result.success}")

    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"- {error}")

    raise SystemExit(0 if result.success else 1)


if __name__ == "__main__":
    main()
