import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.aerial_housing_detection.domain.losses import LossCalculator, OperationalArea
from src.aerial_housing_detection.storage.loss_repository import LossRepository

REQUIRED_COLUMNS = {
    "area_id",
    "transformer_code",
    "latitude",
    "longitude",
    "neighborhood",
    "city",
    "feeder",
    "customer_count",
    "reference_month",
    "injected_energy_kwh",
    "billed_consumption_kwh",
}


@dataclass(frozen=True)
class LossImportResult:
    input_path: Path
    imported_rows: int
    skipped_rows: int
    errors: list[str]

    @property
    def success(self) -> bool:
        return not self.errors


class LossCsvImporter:
    def __init__(
        self,
        repository: LossRepository | None = None,
        calculator: LossCalculator | None = None,
    ) -> None:
        self.repository = repository or LossRepository()
        self.calculator = calculator or LossCalculator()

    def import_csv(self, input_path: Path) -> LossImportResult:
        errors: list[str] = []
        imported_rows = 0
        skipped_rows = 0

        if not input_path.exists():
            return LossImportResult(
                input_path=input_path,
                imported_rows=0,
                skipped_rows=0,
                errors=[f"File not found: {input_path}"],
            )

        self.repository.initialize()

        with input_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            missing_columns = self._missing_columns(reader.fieldnames)

            if missing_columns:
                return LossImportResult(
                    input_path=input_path,
                    imported_rows=0,
                    skipped_rows=0,
                    errors=[
                        "Missing required columns: "
                        + ", ".join(sorted(missing_columns))
                    ],
                )

            for row_number, row in enumerate(reader, start=2):
                try:
                    area = self._build_area(row)
                    record = self.calculator.calculate_record(
                        area_id=area.area_id,
                        reference_month=self._get_required_text(
                            row,
                            "reference_month",
                        ),
                        injected_energy_kwh=self._get_required_float(
                            row,
                            "injected_energy_kwh",
                        ),
                        billed_consumption_kwh=self._get_required_float(
                            row,
                            "billed_consumption_kwh",
                        ),
                    )

                    self.repository.save_area(area)
                    self.repository.save_monthly_loss_record(record)
                    imported_rows += 1

                except ValueError as exc:
                    skipped_rows += 1
                    errors.append(f"row {row_number}: {exc}")

        return LossImportResult(
            input_path=input_path,
            imported_rows=imported_rows,
            skipped_rows=skipped_rows,
            errors=errors,
        )

    def _missing_columns(self, fieldnames: list[str] | None) -> set[str]:
        if not fieldnames:
            return set(REQUIRED_COLUMNS)

        normalized_fieldnames = {fieldname.strip() for fieldname in fieldnames}
        return REQUIRED_COLUMNS - normalized_fieldnames

    def _build_area(self, row: dict[str, Any]) -> OperationalArea:
        return OperationalArea(
            area_id=self._get_required_text(row, "area_id"),
            transformer_code=self._get_required_text(row, "transformer_code"),
            latitude=self._get_required_float(row, "latitude"),
            longitude=self._get_required_float(row, "longitude"),
            neighborhood=self._get_required_text(row, "neighborhood"),
            city=self._get_required_text(row, "city"),
            feeder=self._get_required_text(row, "feeder"),
            customer_count=self._get_required_int(row, "customer_count"),
        )

    def _get_required_text(self, row: dict[str, Any], key: str) -> str:
        value = row.get(key)

        if value is None or str(value).strip() == "":
            raise ValueError(f"{key} is required")

        return str(value).strip()

    def _get_required_float(self, row: dict[str, Any], key: str) -> float:
        value = self._get_required_text(row, key)

        try:
            return float(value.replace(",", "."))
        except ValueError as exc:
            raise ValueError(f"{key} must be a valid number") from exc

    def _get_required_int(self, row: dict[str, Any], key: str) -> int:
        value = self._get_required_text(row, key)

        try:
            return int(value)
        except ValueError as exc:
            raise ValueError(f"{key} must be a valid integer") from exc
