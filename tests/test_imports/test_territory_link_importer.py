from pathlib import Path

from src.aerial_housing_detection.domain.territory import (
    CensusSector,
    SocialAssistanceTerritory,
)
from src.aerial_housing_detection.imports.territory_link_importer import (
    TerritoryLinkCsvImporter,
)
from src.aerial_housing_detection.storage.territory_repository import (
    TerritoryRepository,
)


def test_territory_link_csv_importer_imports_valid_file(tmp_path: Path) -> None:
    database_path = tmp_path / "area51.db"
    repository = TerritoryRepository(database_path=database_path)
    repository.initialize()

    repository.save_census_sector(
        CensusSector(
            sector_id="sector-001",
            city="Paulista",
            state="PE",
            neighborhood="Maranguape I",
            population=480,
            households=120,
            average_residents_per_household=4.0,
        )
    )
    repository.save_social_assistance_territory(
        SocialAssistanceTerritory(
            territory_id="cras-territory-001",
            cras_code="CRAS-001",
            cras_name="CRAS Maranguape",
            city="Paulista",
            state="PE",
            neighborhood="Maranguape I",
            assisted_families=80,
            vulnerable_families=50,
        )
    )

    input_path = tmp_path / "territory_links.csv"
    input_path.write_text(
        "\n".join(
            [
                "area_id,sector_id,territory_id",
                "area-001,sector-001,cras-territory-001",
            ]
        ),
        encoding="utf-8",
    )

    importer = TerritoryLinkCsvImporter(repository=repository)

    result = importer.import_csv(input_path)
    indicator = repository.build_territorial_indicator(
        area_id="area-001",
        estimated_roofs=145,
        customer_count=120,
    )

    assert result.success
    assert result.imported_rows == 1
    assert result.skipped_rows == 0
    assert indicator is not None
    assert indicator.area_id == "area-001"
    assert indicator.roof_customer_gap == 25


def test_territory_link_csv_importer_reports_missing_columns(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "area51.db"
    repository = TerritoryRepository(database_path=database_path)
    repository.initialize()

    input_path = tmp_path / "invalid_territory_links.csv"
    input_path.write_text(
        "area_id,sector_id\narea-001,sector-001\n",
        encoding="utf-8",
    )

    importer = TerritoryLinkCsvImporter(repository=repository)

    result = importer.import_csv(input_path)

    assert not result.success
    assert result.imported_rows == 0
    assert result.skipped_rows == 0
    assert result.errors
    assert "Missing required columns" in result.errors[0]
