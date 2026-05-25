import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.aerial_housing_detection.domain.solar import SolarAreaEstimate
from src.aerial_housing_detection.storage.solar_repository import SolarRepository

REQUIRED_COLUMNS = {
    "area_id",
    "reference_month",
    "solar_panel_count",
    "estimated_solar_area_m2",
    "estimated_generation_kwh",
    "confidence_score",
}


@dataclass(frozen=True)
class SolarImportResult:
    input_path: Path
    imported_rows: int
    skipped_rows: int
    errors: list[str]

    @property
    def success(self) -> bool:
        return not self.errors


class SolarCsvImporter:
    def __init__(self, repository: SolarRepository | None = None) -> None:
        self.repository = repository or SolarRepository()

    def import_csv(self, input_path: Path) -> SolarImportResult:
        errors: list[str] = []
        imported_rows = 0
        skipped_rows = 0

        if not input_path.exists():
            return SolarImportResult(
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
                return SolarImportResult(
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
                    estimate = self._build_estimate(row)
                    self.repository.save_estimate(estimate)
                    imported_rows += 1
                except ValueError as exc:
                    skipped_rows += 1
                    errors.append(f"row {row_number}: {exc}")

        return SolarImportResult(
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

    def _build_estimate(self, row: dict[str, Any]) -> SolarAreaEstimate:
        return SolarAreaEstimate(
            area_id=self._get_required_text(row, "area_id"),
            reference_month=self._get_required_text(row, "reference_month"),
            solar_panel_count=self._get_required_int(row, "solar_panel_count"),
            estimated_solar_area_m2=self._get_required_float(
                row,
                "estimated_solar_area_m2",
            ),
            estimated_generation_kwh=self._get_required_float(
                row,
                "estimated_generation_kwh",
            ),
            confidence_score=self._get_required_float(row, "confidence_score"),
        )

    def _get_required_text(self, row: dict[str, Any], key: str) -> str:
        value = row.get(key)

        if value is None or str(value).strip() == "":
            raise ValueError(f"{key} is required")

        return str(value).strip()

    def _get_required_int(self, row: dict[str, Any], key: str) -> int:
        value = self._get_required_text(row, key)

        try:
            return int(value)
        except ValueError as exc:
            raise ValueError(f"{key} must be a valid integer") from exc

    def _get_required_float(self, row: dict[str, Any], key: str) -> float:
        value = self._get_required_text(row, key)

        try:
            return float(value.replace(",", "."))
        except ValueError as exc:
            raise ValueError(f"{key} must be a valid number") from exc
