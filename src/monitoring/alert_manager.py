import json
import threading
import uuid
from pathlib import Path
from typing import Any

from src.monitoring.models import Alert, AlertSeverity, AlertStatus


class AlertManager:
    """Gerencia alertas do sistema de identificação aérea."""

    DEFAULT_LOG_DIR = Path("logs/alerts")
    DEFAULT_FILENAME = "alerts.jsonl"

    def __init__(
        self,
        log_dir: str | Path | None = None,
        filename: str = DEFAULT_FILENAME,
    ) -> None:
        self._log_dir = Path(log_dir) if log_dir else self.DEFAULT_LOG_DIR
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._filepath = self._log_dir / filename
        self._lock = threading.Lock()
        self._handlers: list[Any] = []

    @property
    def filepath(self) -> Path:
        return self._filepath

    # ------------------------------------------------------------------
    # Disparo
    # ------------------------------------------------------------------

    def fire(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        source: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> Alert:
        alert = Alert(
            id=uuid.uuid4().hex,
            title=title,
            message=message,
            severity=severity,
            source=source,
            metadata=metadata or {},
        )

        self._persist(alert)
        self._notify_handlers(alert)

        return alert

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def register_handler(self, handler: Any) -> None:
        self._handlers.append(handler)

    # ------------------------------------------------------------------
    # Leitura
    # ------------------------------------------------------------------

    def get_all(self) -> list[dict[str, Any]]:
        if not self._filepath.exists():
            return []

        alerts: list[dict[str, Any]] = []
        with open(self._filepath, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        alerts.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        return alerts

    def get_alerts(
        self,
        limit: int = 50,
        unacknowledged_only: bool = False,
    ) -> list[dict[str, Any]]:
        """Retorna alertas com filtro opcional (usado pelo router)."""
        alerts = self.get_all()

        if unacknowledged_only:
            alerts = [
                a for a in alerts
                if a.get("status") != AlertStatus.ACKNOWLEDGED.value
            ]

        return alerts[-limit:]

    def get_by_severity(self, severity: AlertSeverity) -> list[dict[str, Any]]:
        return [
            a for a in self.get_all()
            if a.get("severity") == severity.value
        ]

    def get_by_source(self, source: str) -> list[dict[str, Any]]:
        return [a for a in self.get_all() if a.get("source") == source]

    def get_open(self) -> list[dict[str, Any]]:
        return [
            a for a in self.get_all()
            if a.get("status") == AlertStatus.OPEN.value
        ]

    def get_critical(self) -> list[dict[str, Any]]:
        critical_levels = {AlertSeverity.ERROR.value, AlertSeverity.CRITICAL.value}
        return [
            a for a in self.get_all()
            if a.get("severity") in critical_levels
        ]

    # ------------------------------------------------------------------
    # Acknowledge
    # ------------------------------------------------------------------

    def acknowledge(self, alert_id: str) -> bool:
        """Marca um alerta como acknowledged pelo ID. Retorna True se encontrou."""
        alerts = self.get_all()
        found = False

        updated: list[dict[str, Any]] = []
        for a in alerts:
            if a.get("id") == alert_id:
                a["status"] = AlertStatus.ACKNOWLEDGED.value
                found = True
            updated.append(a)

        if found:
            self._rewrite_all(updated)

        return found

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------

    def count(self) -> int:
        return len(self.get_all())

    def clear(self) -> None:
        with self._lock:
            if self._filepath.exists():
                self._filepath.unlink()

    # ------------------------------------------------------------------
    # Persistência
    # ------------------------------------------------------------------

    def _persist(self, alert: Alert) -> None:
        with self._lock, open(self._filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(alert.to_dict(), ensure_ascii=False) + "\n")

    def _rewrite_all(self, alerts: list[dict[str, Any]]) -> None:
        """Reescreve todo o arquivo (usado no acknowledge)."""
        with self._lock, open(self._filepath, "w", encoding="utf-8") as f:
            for a in alerts:
                f.write(json.dumps(a, ensure_ascii=False) + "\n")

    def _notify_handlers(self, alert: Alert) -> None:
        for handler in self._handlers:
            try:
                handler.handle(alert)
            except Exception:
                pass
