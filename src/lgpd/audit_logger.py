import uuid
from datetime import datetime, timezone, timedelta
from threading import Lock
from typing import Optional

from src.lgpd.config import lgpd_settings
from src.lgpd.models import AuditEntry


class AuditLogger:
    def __init__(self) -> None:
        self.retention_days = lgpd_settings.audit_log_retention_days
        self._entries: list[AuditEntry] = []
        self._lock = Lock()

    def log(
        self,
        action: str,
        user: str,
        resource: str,
        detail: str = "",
        ip_address: str = "",
    ) -> AuditEntry:
        entry = AuditEntry(
            id=uuid.uuid4().hex[:12],
            action=action,
            user=user,
            resource=resource,
            detail=detail,
            ip_address=ip_address,
            timestamp=datetime.now(timezone.utc),
        )

        with self._lock:
            self._entries.append(entry)

        return entry

    def get_entries(
        self,
        limit: int = 100,
        user: Optional[str] = None,
        action: Optional[str] = None,
    ) -> list[dict]:
        with self._lock:
            entries = list(self._entries)

        if user:
            entries = [e for e in entries if e.user == user]
        if action:
            entries = [e for e in entries if e.action == action]

        entries.sort(key=lambda e: e.timestamp, reverse=True)
        return [e.to_dict() for e in entries[:limit]]

    def purge_expired(self) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.retention_days)

        with self._lock:
            before = len(self._entries)
            self._entries = [e for e in self._entries if e.timestamp > cutoff]
            return before - len(self._entries)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
