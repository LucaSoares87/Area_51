from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class ReportOutput:
    """Represents generated output files for one analysis."""

    analysis_id: str
    csv_report_path: Path
    html_map_path: Path
    generated_at: datetime = datetime.now(UTC)

    def to_dict(self) -> dict[str, str]:
        """Return serializable report output data."""
        return {
            "analysis_id": self.analysis_id,
            "csv_report_path": str(self.csv_report_path),
            "html_map_path": str(self.html_map_path),
            "generated_at": self.generated_at.isoformat(),
        }


@dataclass(frozen=True)
class PipelineResult:
    """Represents the complete pipeline output."""

    analysis_id: str
    estimated_residences: int
    roof_count: int
    confidence_score: float
    csv_report_path: Path
    html_map_path: Path

    def to_dict(self) -> dict[str, object]:
        """Return serializable pipeline result."""
        return {
            "analysis_id": self.analysis_id,
            "estimated_residences": self.estimated_residences,
            "roof_count": self.roof_count,
            "confidence_score": self.confidence_score,
            "csv_report_path": str(self.csv_report_path),
            "html_map_path": str(self.html_map_path),
        }
