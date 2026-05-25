import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.aerial_housing_detection.domain.territory import CensusSector
from src.aerial_housing_detection.storage.territory_repository import (
    TerritoryRepository,
)

REQUIRED_COLUMNS = {
    "sector_id",
    "city",
    "state",
    "neighborhood",
    "population",
    "households",
    "average_residents_per_household",
}


@dataclass(frozen=True)
class IbgeImportResult:
    input_path: Path
    imported_rows: int
    skipped_rows: int
    errors: list[str]

    @property
    def success(self) -> bool:
        return not self.errors


class IbgeCsvImporter:
    def __init__(self, repository: TerritoryRepository | None = None) -> None:
        self.repository = repository or TerritoryRepository()

    def import_csv(self, input_path: Path) -> IbgeImportResult:
        errors: list[str] = []
        imported_rows = 0
        skipped_rows = 0

        if not input_path.exists():
            return IbgeImportResult(
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
                return IbgeImportResult(
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
                    sector = self._build_sector(row)
                    self.repository.save_census_sector(sector)
                    imported_rows += 1

                except ValueError as exc:
                    skipped_rows += 1
                    errors.append(f"row {row_number}: {exc}")

        return IbgeImportResult(
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

    def _build_sector(self, row: dict[str, Any]) -> CensusSector:
        return CensusSector(
            sector_id=self._get_required_text(row, "sector_id"),
            city=self._get_required_text(row, "city"),
            state=self._get_required_text(row, "state"),
            neighborhood=self._get_required_text(row, "neighborhood"),
            population=self._get_required_int(row, "population"),
            households=self._get_required_int(row, "households"),
            average_residents_per_household=self._get_required_float(
                row,
                "average_residents_per_household",
            ),
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
