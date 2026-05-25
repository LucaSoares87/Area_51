import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.aerial_housing_detection.domain.territory import OperationalTerritoryLink
from src.aerial_housing_detection.storage.territory_repository import (
    TerritoryRepository,
)

REQUIRED_COLUMNS = {
    "area_id",
    "sector_id",
    "territory_id",
}


@dataclass(frozen=True)
class TerritoryLinkImportResult:
    input_path: Path
    imported_rows: int
    skipped_rows: int
    errors: list[str]

    @property
    def success(self) -> bool:
        return not self.errors


class TerritoryLinkCsvImporter:
    def __init__(self, repository: TerritoryRepository | None = None) -> None:
        self.repository = repository or TerritoryRepository()

    def import_csv(self, input_path: Path) -> TerritoryLinkImportResult:
        errors: list[str] = []
        imported_rows = 0
        skipped_rows = 0

        if not input_path.exists():
            return TerritoryLinkImportResult(
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
                return TerritoryLinkImportResult(
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
                    link = self._build_link(row)
                    self.repository.save_operational_link(link)
                    imported_rows += 1
                except ValueError as exc:
                    skipped_rows += 1
                    errors.append(f"row {row_number}: {exc}")

        return TerritoryLinkImportResult(
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

    def _build_link(self, row: dict[str, Any]) -> OperationalTerritoryLink:
        return OperationalTerritoryLink(
            area_id=self._get_required_text(row, "area_id"),
            sector_id=self._get_required_text(row, "sector_id"),
            territory_id=self._get_required_text(row, "territory_id"),
        )

    def _get_required_text(self, row: dict[str, Any], key: str) -> str:
        value = row.get(key)

        if value is None or str(value).strip() == "":
            raise ValueError(f"{key} is required")

        return str(value).strip()
