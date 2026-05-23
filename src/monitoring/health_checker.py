from datetime import UTC, datetime

from src.detect.config import detect_settings
from src.monitoring.config import monitoring_settings
from src.monitoring.models import ComponentHealth, ComponentHealthSchema, HealthStatus


class HealthChecker:
    def check(self) -> HealthStatus:
        components = [
            self._check_models(),
            self._check_uploads_dir(),
            self._check_metrics_dir(),
        ]

        overall = "healthy"
        for comp in components:
            if comp.status == "unhealthy":
                overall = "unhealthy"
                break
            if comp.status == "degraded":
                overall = "degraded"

        return HealthStatus(
            status=overall,
            components=[
                ComponentHealthSchema(
                    name=c.name,
                    status=c.status,
                    detail=c.detail,
                )
                for c in components
            ],
            checked_at=datetime.now(UTC),
        )

    def _check_models(self) -> ComponentHealth:
        spacenet = detect_settings.spacenet_model_path
        bootstrap = detect_settings.bootstrap_model_path

        if detect_settings.mock_inference:
            return ComponentHealth(
                name="models",
                status="healthy",
                detail="Mock inference ativo, modelos nao necessarios",
            )

        missing = []
        if not spacenet.exists():
            missing.append(str(spacenet))
        if not bootstrap.exists():
            missing.append(str(bootstrap))

        if missing:
            return ComponentHealth(
                name="models",
                status="unhealthy",
                detail=f"Modelos ausentes: {missing}",
            )

        return ComponentHealth(
            name="models",
            status="healthy",
            detail="Todos os modelos carregados",
        )

    def _check_uploads_dir(self) -> ComponentHealth:
        path = detect_settings.uploads_dir
        if not path.exists():
            return ComponentHealth(
                name="uploads_dir",
                status="degraded",
                detail=f"Diretorio nao encontrado: {path}",
            )
        return ComponentHealth(
            name="uploads_dir",
            status="healthy",
            detail=str(path),
        )

    def _check_metrics_dir(self) -> ComponentHealth:
        path = monitoring_settings.metrics_dir
        if not path.exists():
            return ComponentHealth(
                name="metrics_dir",
                status="degraded",
                detail=f"Diretorio nao encontrado: {path}",
            )
        return ComponentHealth(
            name="metrics_dir",
            status="healthy",
            detail=str(path),
        )
