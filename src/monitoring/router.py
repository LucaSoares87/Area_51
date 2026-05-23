from fastapi import APIRouter, Depends, HTTPException, status

from src.auth.dependencies import get_current_user, require_admin, require_analyst
from src.auth.models import User
from src.monitoring.alert_manager import AlertManager
from src.monitoring.config import monitoring_settings
from src.monitoring.drift_detector import DriftDetector
from src.monitoring.health_checker import HealthChecker
from src.monitoring.metrics_exporter import MetricsExporter
from src.monitoring.models import AlertSeverity, ExportedMetrics, HealthStatus
from src.monitoring.prediction_logger import PredictionLogger

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])

prediction_logger = PredictionLogger()
drift_detector = DriftDetector()
alert_manager = AlertManager()
health_checker = HealthChecker()
metrics_exporter = MetricsExporter(prediction_logger, drift_detector)

_reference_confidences: list[float] = []


@router.get("/health", response_model=HealthStatus)
async def health(user: User = Depends(get_current_user)):
    return health_checker.check()


@router.get("/metrics", response_model=ExportedMetrics)
async def get_metrics(user: User = Depends(require_analyst)):
    return metrics_exporter.export(reference_confidences=_reference_confidences)


@router.get("/metrics/aggregated")
async def get_aggregated(user: User = Depends(require_analyst)):
    return prediction_logger.aggregate()


@router.get("/predictions")
async def get_predictions(
    limit: int = 100,
    user: User = Depends(require_analyst),
):
    return prediction_logger.get_logs(limit=limit)


@router.post("/drift/check")
async def check_drift(user: User = Depends(require_analyst)):
    current = prediction_logger.get_confidences()
    if not _reference_confidences:
        return {"message": "Baseline de referencia nao definido"}
    report = drift_detector.detect(_reference_confidences, current)
    if report.drifted:
        alert_manager.fire(
            title="Drift detectado",
            message=report.message,
            severity=AlertSeverity.WARNING,
            source="drift_detector",
        )
    return report


@router.post("/drift/baseline")
async def set_baseline(user: User = Depends(require_admin)):
    global _reference_confidences
    _reference_confidences = prediction_logger.get_confidences()
    return {
        "message": "Baseline definido",
        "samples": len(_reference_confidences),
    }


@router.get("/alerts")
async def get_alerts(
    limit: int = 50,
    unacknowledged_only: bool = False,
    user: User = Depends(require_analyst),
):
    return alert_manager.get_alerts(limit=limit, unacknowledged_only=unacknowledged_only)


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    user: User = Depends(require_analyst),
):
    if not alert_manager.acknowledge(alert_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta nao encontrado",
        )
    return {"message": "Alerta reconhecido"}


@router.get("/config")
async def get_monitoring_config(user: User = Depends(require_admin)):
    return {
        "log_retention_days": monitoring_settings.log_retention_days,
        "drift_check_interval_hours": monitoring_settings.drift_check_interval_hours,
        "drift_psi_threshold": monitoring_settings.drift_psi_threshold,
        "drift_min_samples": monitoring_settings.drift_min_samples,
        "alert_cooldown_minutes": monitoring_settings.alert_cooldown_minutes,
        "prediction_log_max_size": monitoring_settings.prediction_log_max_size,
    }
