from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class MonitoringSettings(BaseSettings):
    """Configurações unificadas do módulo de monitoramento."""

    # Diretórios
    metrics_dir: Path = Path("data/metrics")

    # Retenção
    log_retention_days: int = 90

    # Drift Detection
    drift_check_interval_hours: int = 24
    drift_psi_threshold: float = 0.2
    drift_min_samples: int = 100

    # Alertas
    confidence_alert_threshold: float = Field(
        default=0.5,
        description="Alerta quando confidence média cai abaixo deste valor.",
    )
    alert_window_minutes: int = Field(
        default=60,
        description="Janela de tempo para calcular métricas de alerta.",
    )
    min_predictions_for_alert: int = Field(
        default=10,
        description="Mínimo de predições na janela para disparar alerta.",
    )
    alert_email_enabled: bool = False
    alert_email_to: str = ""
    alert_webhook_url: str = ""
    alert_cooldown_minutes: int = 60

    # Health
    health_check_timeout_seconds: int = 5

    # Export
    metrics_export_enabled: bool = True
    metrics_export_format: str = "json"

    # Prediction log
    prediction_log_max_size: int = 10_000

    model_config = {
        "env_prefix": "MONITOR_",
        "env_file": ".env",
        "extra": "ignore",
    }


monitoring_settings = MonitoringSettings()
