from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class AlertSeverity(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class DriftStatus(str, Enum):
    STABLE = "stable"
    WARNING = "warning"
    DRIFTED = "drifted"


@dataclass
class Alert:
    id: str = ""
    title: str = ""
    message: str = ""
    severity: AlertSeverity = AlertSeverity.INFO
    source: str = ""
    status: AlertStatus = AlertStatus.OPEN
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_critical(self) -> bool:
        return self.severity in (AlertSeverity.ERROR, AlertSeverity.CRITICAL)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "severity": self.severity.value,
            "source": self.source,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class PredictionRecord:
    confidence: float = 0.0
    predicted_class: str = ""
    true_class: str | None = None
    source: str = "inference"
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "confidence": round(self.confidence, 6),
            "predicted_class": self.predicted_class,
            "true_class": self.true_class,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class DriftReport:
    psi: Optional[float] = None
    threshold: float = 0.2
    drifted: bool = False
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    analyzed_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    @property
    def status(self) -> DriftStatus:
        if self.psi is None:
            return DriftStatus.STABLE
        if self.drifted:
            return DriftStatus.DRIFTED
        if self.psi > self.threshold * 0.75:
            return DriftStatus.WARNING
        return DriftStatus.STABLE

    def to_dict(self) -> dict[str, Any]:
        return {
            "psi": self.psi,
            "threshold": self.threshold,
            "drifted": self.drifted,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "analyzed_at": self.analyzed_at.isoformat(),
        }


@dataclass
class ComponentHealth:
    name: str = ""
    status: str = "healthy"
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "detail": self.detail,
        }


class ComponentHealthSchema(BaseModel):
    name: str
    status: str
    detail: str = ""


class HealthStatus(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    components: list[ComponentHealthSchema] = []
    checked_at: datetime


class DriftReportSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    psi: Optional[float] = None
    threshold: float
    drifted: bool
    status: str = ""
    message: str = ""
    details: dict[str, Any] = {}
    analyzed_at: datetime


class ExportedMetrics(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    aggregated: dict[str, Any] = {}
    drift: Optional[DriftReportSchema] = None
    exported_at: datetime
