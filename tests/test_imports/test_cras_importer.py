from pathlib import Path

from src.aerial_housing_detection.imports.cras_importer import CrasCsvImporter
from src.aerial_housing_detection.storage.territory_repository import (
    TerritoryRepository,
)


def test_cras_csv_importer_imports_valid_file(tmp_path: Path) -> None:
    input_path = tmp_path / "cras_territories.csv"
    input_path.write_text(
        "\n".join(
            [
                (
                    "territory_id,cras_code,cras_name,city,state,neighborhood,"
                    "assisted_families,vulnerable_families"
                ),
                (
                    "cras-territory-001,CRAS-001,CRAS Maranguape,Paulista,PE,"
                    "Maranguape I,80,50"
                ),
            ]
        ),
        encoding="utf-8",
    )

    repository = TerritoryRepository(database_path=tmp_path / "area51.db")
    importer = CrasCsvImporter(repository=repository)

    result = importer.import_csv(input_path)

    assert result.success
    assert result.imported_rows == 1
    assert result.skipped_rows == 0


def test_cras_csv_importer_reports_missing_columns(tmp_path: Path) -> None:
    input_path = tmp_path / "invalid_cras_territories.csv"
    input_path.write_text(
        "territory_id,cras_code\ncras-territory-001,CRAS-001\n",
        encoding="utf-8",
    )

    repository = TerritoryRepository(database_path=tmp_path / "area51.db")
    importer = CrasCsvImporter(repository=repository)

    result = importer.import_csv(input_path)

    assert not result.success
    assert result.imported_rows == 0
    assert result.skipped_rows == 0
    assert result.errors
    assert "Missing required columns" in result.errors[0]
