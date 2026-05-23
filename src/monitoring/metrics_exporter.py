import json
from datetime import UTC, datetime
from pathlib import Path

from src.monitoring.config import monitoring_settings
from src.monitoring.drift_detector import DriftDetector
from src.monitoring.models import DriftReportSchema, ExportedMetrics
from src.monitoring.prediction_logger import PredictionLogger


class MetricsExporter:
    def __init__(
        self,
        logger: PredictionLogger,
        drift_detector: DriftDetector,
    ):
        self.logger = logger
        self.drift_detector = drift_detector
        self.output_dir = monitoring_settings.metrics_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(self, reference_confidences: list[float] | None = None) -> ExportedMetrics:
        aggregated = self.logger.aggregate()
        current_confidences = self.logger.get_confidences()

        drift_schema = None
        if reference_confidences and current_confidences:
            report = self.drift_detector.detect(
                reference_confidences, current_confidences
            )
            drift_schema = DriftReportSchema(
                psi=report.psi,
                threshold=report.threshold,
                drifted=report.drifted,
                status=report.status.value,
                message=report.message,
                details=report.details,
                analyzed_at=report.analyzed_at,
            )

        exported = ExportedMetrics(
            aggregated=aggregated,
            drift=drift_schema,
            exported_at=datetime.now(UTC),
        )

        self._save(exported)
        return exported

    def _save(self, metrics: ExportedMetrics) -> Path:
        timestamp = metrics.exported_at.strftime("%Y%m%d_%H%M%S")
        filename = f"metrics_{timestamp}.json"
        output_path = self.output_dir / filename

        output_path.write_text(
            json.dumps(
                metrics.model_dump(),
                default=str,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        return output_path
