from pathlib import Path

from src.aerial_housing_detection.imports.loss_importer import LossCsvImporter
from src.aerial_housing_detection.storage.loss_repository import LossRepository


def test_loss_csv_importer_imports_valid_file(tmp_path: Path) -> None:
    input_path = tmp_path / "monthly_losses.csv"
    input_path.write_text(
        "\n".join(
            [
                (
                    "area_id,transformer_code,latitude,longitude,neighborhood,"
                    "city,feeder,customer_count,reference_month,"
                    "injected_energy_kwh,billed_consumption_kwh"
                ),
                (
                    "area-001,TR-001,-7.9401,-34.8734,Maranguape I,"
                    "Paulista,AL-01,120,2026-05,12000,8300"
                ),
            ]
        ),
        encoding="utf-8",
    )

    repository = LossRepository(database_path=tmp_path / "area51.db")
    importer = LossCsvImporter(repository=repository)

    result = importer.import_csv(input_path)
    records = repository.list_monthly_loss_records(reference_month="2026-05")

    assert result.success
    assert result.imported_rows == 1
    assert result.skipped_rows == 0
    assert len(records) == 1
    assert records[0]["area_id"] == "area-001"
    assert records[0]["estimated_loss_kwh"] == 3700.0


def test_loss_csv_importer_reports_missing_columns(tmp_path: Path) -> None:
    input_path = tmp_path / "invalid_monthly_losses.csv"
    input_path.write_text(
        "area_id,transformer_code\narea-001,TR-001\n",
        encoding="utf-8",
    )

    repository = LossRepository(database_path=tmp_path / "area51.db")
    importer = LossCsvImporter(repository=repository)

    result = importer.import_csv(input_path)

    assert not result.success
    assert result.imported_rows == 0
    assert result.skipped_rows == 0
    assert result.errors
    assert "Missing required columns" in result.errors[0]


def test_loss_csv_importer_uses_historical_recurrence(tmp_path: Path) -> None:
    repository = LossRepository(database_path=tmp_path / "area51.db")
    repository.initialize()

    first_input_path = tmp_path / "monthly_losses_2026_04.csv"
    first_input_path.write_text(
        "\n".join(
            [
                (
                    "area_id,transformer_code,latitude,longitude,neighborhood,"
                    "city,feeder,customer_count,reference_month,"
                    "injected_energy_kwh,billed_consumption_kwh"
                ),
                (
                    "area-001,TR-001,-7.9401,-34.8734,Maranguape I,"
                    "Paulista,AL-01,120,2026-04,12000,8300"
                ),
            ]
        ),
        encoding="utf-8",
    )

    second_input_path = tmp_path / "monthly_losses_2026_05.csv"
    second_input_path.write_text(
        "\n".join(
            [
                (
                    "area_id,transformer_code,latitude,longitude,neighborhood,"
                    "city,feeder,customer_count,reference_month,"
                    "injected_energy_kwh,billed_consumption_kwh"
                ),
                (
                    "area-001,TR-001,-7.9401,-34.8734,Maranguape I,"
                    "Paulista,AL-01,120,2026-05,12000,8300"
                ),
            ]
        ),
        encoding="utf-8",
    )

    importer = LossCsvImporter(repository=repository)

    first_result = importer.import_csv(first_input_path)
    first_records = repository.list_monthly_loss_records(reference_month="2026-04")

    second_result = importer.import_csv(second_input_path)
    second_records = repository.list_monthly_loss_records(reference_month="2026-05")

    assert first_result.success
    assert second_result.success
    assert len(first_records) == 1
    assert len(second_records) == 1
    assert second_records[0]["priority_score"] > first_records[0]["priority_score"]
