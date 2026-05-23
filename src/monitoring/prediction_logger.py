import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.monitoring.models import PredictionRecord


class PredictionLogger:
    """Registra predições em arquivo JSONL para auditoria e drift detection."""

    DEFAULT_LOG_DIR = Path("logs/predictions")
    DEFAULT_FILENAME = "predictions.jsonl"

    def __init__(
        self,
        log_dir: str | Path | None = None,
        filename: str = DEFAULT_FILENAME,
        max_buffer_size: int = 100,
    ) -> None:
        self._log_dir = Path(log_dir) if log_dir else self.DEFAULT_LOG_DIR
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._filepath = self._log_dir / filename
        self._max_buffer_size = max_buffer_size
        self._buffer: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    @property
    def filepath(self) -> Path:
        return self._filepath

    # ------------------------------------------------------------------
    # Escrita
    # ------------------------------------------------------------------

    def log(
        self,
        confidence: float,
        predicted_class: str,
        true_class: str | None = None,
        source: str = "inference",
        metadata: dict[str, Any] | None = None,
    ) -> PredictionRecord:
        record = PredictionRecord(
            confidence=confidence,
            predicted_class=predicted_class,
            true_class=true_class,
            source=source,
            metadata=metadata or {},
        )

        with self._lock:
            self._buffer.append(record.to_dict())
            if len(self._buffer) >= self._max_buffer_size:
                self._flush_buffer()

        return record

    def flush(self) -> int:
        with self._lock:
            return self._flush_buffer()

    def _flush_buffer(self) -> int:
        if not self._buffer:
            return 0

        count = len(self._buffer)
        with open(self._filepath, "a", encoding="utf-8") as f:
            for record_dict in self._buffer:
                f.write(json.dumps(record_dict, ensure_ascii=False) + "\n")

        self._buffer.clear()
        return count

    # ------------------------------------------------------------------
    # Leitura
    # ------------------------------------------------------------------

    def read_all(self) -> list[dict[str, Any]]:
        self.flush()

        if not self._filepath.exists():
            return []

        records: list[dict[str, Any]] = []
        with open(self._filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        return records

    def read_recent(self, n: int = 100) -> list[dict[str, Any]]:
        all_records = self.read_all()
        return all_records[-n:]

    def read_by_source(self, source: str) -> list[dict[str, Any]]:
        return [r for r in self.read_all() if r.get("source") == source]

    def get_logs(self, limit: int = 100) -> list[dict[str, Any]]:
        """Retorna os últimos `limit` registros (usado pelo router)."""
        return self.read_recent(limit)

    def get_confidences(self) -> list[float]:
        """Extrai lista de confidences de todos os registros."""
        return [
            r["confidence"]
            for r in self.read_all()
            if "confidence" in r
        ]

    def aggregate(self) -> dict[str, Any]:
        """Calcula métricas agregadas sobre as predições."""
        records = self.read_all()

        if not records:
            return {
                "total_predictions": 0,
                "avg_confidence": 0.0,
                "min_confidence": 0.0,
                "max_confidence": 0.0,
                "classes": {},
                "sources": {},
            }

        confidences = [r.get("confidence", 0.0) for r in records]

        # Contagem por classe predita
        classes: dict[str, int] = {}
        for r in records:
            cls = r.get("predicted_class", "unknown")
            classes[cls] = classes.get(cls, 0) + 1

        # Contagem por source
        sources: dict[str, int] = {}
        for r in records:
            src = r.get("source", "unknown")
            sources[src] = sources.get(src, 0) + 1

        return {
            "total_predictions": len(records),
            "avg_confidence": round(sum(confidences) / len(confidences), 6),
            "min_confidence": round(min(confidences), 6),
            "max_confidence": round(max(confidences), 6),
            "classes": classes,
            "sources": sources,
        }

    def count(self) -> int:
        return len(self.read_all())

    def clear(self) -> None:
        with self._lock:
            self._buffer.clear()
            if self._filepath.exists():
                self._filepath.unlink()

    def __del__(self) -> None:
        try:
            self.flush()
        except Exception:
            pass
