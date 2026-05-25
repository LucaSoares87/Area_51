from pathlib import Path

from src.aerial_housing_detection.imports.solar_importer import SolarCsvImporter
from src.aerial_housing_detection.storage.solar_repository import SolarRepository


def test_solar_csv_importer_imports_valid_file(tmp_path: Path) -> None:
    input_path = tmp_path / "solar_estimates.csv"
    input_path.write_text(
        "\n".join(
            [
                (
                    "area_id,reference_month,solar_panel_count,"
                    "estimated_solar_area_m2,estimated_generation_kwh,"
                    "confidence_score"
                ),
                "area-001,2026-05,18,72.0,950.0,0.86",
            ]
        ),
        encoding="utf-8",
    )

    repository = SolarRepository(database_path=tmp_path / "area51.db")
    importer = SolarCsvImporter(repository=repository)

    result = importer.import_csv(input_path)
    estimate = repository.get_estimate(
        area_id="area-001",
        reference_month="2026-05",
    )

    assert result.success
    assert result.imported_rows == 1
    assert result.skipped_rows == 0
    assert estimate is not None
    assert estimate["estimated_generation_kwh"] == 950.0


def test_solar_csv_importer_reports_missing_columns(tmp_path: Path) -> None:
    input_path = tmp_path / "invalid_solar_estimates.csv"
    input_path.write_text(
        "area_id,reference_month\narea-001,2026-05\n",
        encoding="utf-8",
    )

    repository = SolarRepository(database_path=tmp_path / "area51.db")
    importer = SolarCsvImporter(repository=repository)

    result = importer.import_csv(input_path)

    assert not result.success
    assert result.imported_rows == 0
    assert result.skipped_rows == 0
    assert result.errors
    assert "Missing required columns" in result.errors[0]
