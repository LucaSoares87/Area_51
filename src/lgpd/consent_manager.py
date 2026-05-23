import uuid
from datetime import UTC, datetime, timedelta
from threading import Lock

from src.lgpd.config import lgpd_settings
from src.lgpd.models import ConsentRecord, ConsentStatus


class ConsentManager:
    def __init__(self) -> None:
        self._records: list[ConsentRecord] = []
        self._lock = Lock()

    def grant(
        self,
        subject_id: str,
        purpose: str,
        granted_by: str = "",
    ) -> ConsentRecord:
        now = datetime.now(UTC)
        expires_at = now + timedelta(days=lgpd_settings.consent_expiry_days)

        record = ConsentRecord(
            consent_id=uuid.uuid4().hex,
            subject_id=subject_id,
            purpose=purpose,
            granted_by=granted_by,
            status=ConsentStatus.GRANTED,
            granted_at=now,
            expires_at=expires_at,
        )

        with self._lock:
            self._records.append(record)

        return record

    def revoke(self, consent_id: str) -> ConsentRecord | None:
        with self._lock:
            for record in self._records:
                if record.consent_id == consent_id:
                    record.revoke()
                    return record
        return None

    def get_by_id(self, consent_id: str) -> ConsentRecord | None:
        with self._lock:
            for record in self._records:
                if record.consent_id == consent_id:
                    return record
        return None

    def get_by_subject(self, subject_id: str) -> list[dict]:
        with self._lock:
            if subject_id == "*":
                return [r.to_dict() for r in self._records]
            return [
                r.to_dict()
                for r in self._records
                if r.subject_id == subject_id
            ]

    def get_active_by_subject(self, subject_id: str) -> list[dict]:
        with self._lock:
            return [
                r.to_dict()
                for r in self._records
                if r.subject_id == subject_id and r.is_valid
            ]

    def count(self) -> int:
        with self._lock:
            return len(self._records)

    def count_active(self) -> int:
        with self._lock:
            return sum(1 for r in self._records if r.is_valid)

    def clear(self) -> None:
        with self._lock:
            self._records.clear()
