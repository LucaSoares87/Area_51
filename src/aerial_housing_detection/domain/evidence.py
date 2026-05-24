from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class OperationalEvidence:
    analysis_id: str
    image_path: Path
    raw_detection_count: int
    filtered_detection_count: int
    final_detection_count: int
    estimated_residences: int
    average_confidence: float
    status: str
    csv_report_path: Path | None = None
    html_map_path: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "image_path": str(self.image_path),
            "raw_detection_count": self.raw_detection_count,
            "filtered_detection_count": self.filtered_detection_count,
            "final_detection_count": self.final_detection_count,
            "estimated_residences": self.estimated_residences,
            "average_confidence": self.average_confidence,
            "status": self.status,
            "csv_report_path": str(self.csv_report_path) if self.csv_report_path else None,
            "html_map_path": str(self.html_map_path) if self.html_map_path else None,
        }
