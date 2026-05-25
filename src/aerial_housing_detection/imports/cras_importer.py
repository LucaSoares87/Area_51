import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.aerial_housing_detection.domain.territory import SocialAssistanceTerritory
from src.aerial_housing_detection.storage.territory_repository import (
    TerritoryRepository,
)

REQUIRED_COLUMNS = {
    "territory_id",
    "cras_code",
    "cras_name",
    "city",
    "state",
    "neighborhood",
    "assisted_families",
    "vulnerable_families",
}


@dataclass(frozen=True)
class CrasImportResult:
    input_path: Path
    imported_rows: int
    skipped_rows: int
    errors: list[str]

    @property
    def success(self) -> bool:
        return not self.errors


class CrasCsvImporter:
    def __init__(self, repository: TerritoryRepository | None = None) -> None:
        self.repository = repository or TerritoryRepository()

    def import_csv(self, input_path: Path) -> CrasImportResult:
        errors: list[str] = []
        imported_rows = 0
        skipped_rows = 0

        if not input_path.exists():
            return CrasImportResult(
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
                return CrasImportResult(
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
                    territory = self._build_territory(row)
                    self.repository.save_social_assistance_territory(territory)
                    imported_rows += 1

                except ValueError as exc:
                    skipped_rows += 1
                    errors.append(f"row {row_number}: {exc}")

        return CrasImportResult(
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

    def _build_territory(self, row: dict[str, Any]) -> SocialAssistanceTerritory:
        return SocialAssistanceTerritory(
            territory_id=self._get_required_text(row, "territory_id"),
            cras_code=self._get_required_text(row, "cras_code"),
            cras_name=self._get_required_text(row, "cras_name"),
            city=self._get_required_text(row, "city"),
            state=self._get_required_text(row, "state"),
            neighborhood=self._get_required_text(row, "neighborhood"),
            assisted_families=self._get_required_int(row, "assisted_families"),
            vulnerable_families=self._get_required_int(row, "vulnerable_families"),
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
