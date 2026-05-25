import argparse
from pathlib import Path

from src.aerial_housing_detection.imports.territory_link_importer import (
    TerritoryLinkCsvImporter,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import operational territory links from CSV.",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="CSV file path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    importer = TerritoryLinkCsvImporter()
    result = importer.import_csv(Path(args.input))

    print("territory_link_import")
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
