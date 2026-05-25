from pathlib import Path

from src.aerial_housing_detection.imports.ibge_importer import IbgeCsvImporter
from src.aerial_housing_detection.storage.territory_repository import (
    TerritoryRepository,
)


def test_ibge_csv_importer_imports_valid_file(tmp_path: Path) -> None:
    input_path = tmp_path / "ibge_sectors.csv"
    input_path.write_text(
        "\n".join(
            [
                (
                    "sector_id,city,state,neighborhood,population,households,"
                    "average_residents_per_household"
                ),
                "sector-001,Paulista,PE,Maranguape I,480,120,4.0",
            ]
        ),
        encoding="utf-8",
    )

    repository = TerritoryRepository(database_path=tmp_path / "area51.db")
    importer = IbgeCsvImporter(repository=repository)

    result = importer.import_csv(input_path)
    indicator = repository.build_territorial_indicator(
        area_id="area-missing",
        estimated_roofs=100,
        customer_count=80,
    )

    assert result.success
    assert result.imported_rows == 1
    assert result.skipped_rows == 0
    assert indicator is None


def test_ibge_csv_importer_reports_missing_columns(tmp_path: Path) -> None:
    input_path = tmp_path / "invalid_ibge_sectors.csv"
    input_path.write_text(
        "sector_id,city\nsector-001,Paulista\n",
        encoding="utf-8",
    )

    repository = TerritoryRepository(database_path=tmp_path / "area51.db")
    importer = IbgeCsvImporter(repository=repository)

    result = importer.import_csv(input_path)

    assert not result.success
    assert result.imported_rows == 0
    assert result.skipped_rows == 0
    assert result.errors
    assert "Missing required columns" in result.errors[0]
