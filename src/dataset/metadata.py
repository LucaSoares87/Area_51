"""Gestão de metadados de rastreabilidade dos tiles."""

import csv
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

METADATA_FIELDS = [
    "tile_name", "source_image", "x", "y",
    "tile_size", "overlap", "timestamp", "label",
]


@dataclass
class TileRecord:
    tile_name: str
    source_image: str
    x: int
    y: int
    tile_size: int
    overlap: int
    timestamp: str
    label: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class TileMetadata:
    """Lê e escreve metadados de tiles em CSV + JSONL."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.csv_path = self.output_dir / "tiles_metadata.csv"
        self.jsonl_path = self.output_dir / "tiles_metadata.jsonl"
        self._buffer: list[TileRecord] = []

    def add(self, record: TileRecord):
        self._buffer.append(record)

    def flush(self) -> int:
        if not self._buffer:
            return 0

        write_header = not self.csv_path.exists()

        with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=METADATA_FIELDS)
            if write_header:
                writer.writeheader()
            for rec in self._buffer:
                writer.writerow(rec.to_dict())

        with open(self.jsonl_path, "a", encoding="utf-8") as f:
            for rec in self._buffer:
                f.write(json.dumps(rec.to_dict(), ensure_ascii=False) + "\n")

        count = len(self._buffer)
        self._buffer.clear()
        return count

    def load_csv(self) -> list[dict]:
        if not self.csv_path.exists():
            return []
        with open(self.csv_path, encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def update_label(self, tile_name: str, label: str) -> bool:
        records = self.load_csv()
        updated = False
        for rec in records:
            if rec["tile_name"] == tile_name:
                rec["label"] = label
                updated = True
                break

        if updated:
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=METADATA_FIELDS)
                writer.writeheader()
                writer.writerows(records)

        return updated

    @staticmethod
    def now_iso() -> str:
        return datetime.now(UTC).isoformat()
