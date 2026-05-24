import json
from pathlib import Path

from config.settings import get_settings
from src.aerial_housing_detection.domain.evidence import OperationalEvidence


class EvidenceGenerator:
    """Generates operational evidence files for pipeline executions."""

    def __init__(self, output_dir: Path | None = None) -> None:
        settings = get_settings()
        self.output_dir = output_dir or settings.reports_dir

    def generate_json(self, evidence: OperationalEvidence) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / f"{evidence.analysis_id}_evidence.json"
        output_path.write_text(
            json.dumps(evidence.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return output_path
