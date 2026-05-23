import uuid
from datetime import UTC, datetime, timedelta
from threading import Lock

from src.lgpd.config import lgpd_settings
from src.lgpd.models import DeletionRequest, DeletionStatus


class DataDeletionService:
    def __init__(self) -> None:
        self._requests: list[DeletionRequest] = []
        self._lock = Lock()

    def create_request(
        self,
        subject_id: str,
        reason: str,
        requested_by: str = "",
    ) -> DeletionRequest:
        now = datetime.now(UTC)
        deadline = now + timedelta(days=lgpd_settings.deletion_max_processing_days)

        request = DeletionRequest(
            id=uuid.uuid4().hex,
            subject_id=subject_id,
            reason=reason,
            requested_by=requested_by,
            status=DeletionStatus.PENDING,
            created_at=now,
            deadline_at=deadline,
        )

        with self._lock:
            self._requests.append(request)

        return request

    def approve(self, request_id: str) -> DeletionRequest | None:
        with self._lock:
            for req in self._requests:
                if req.id == request_id and req.status == DeletionStatus.PENDING:
                    req.status = DeletionStatus.APPROVED
                    req.approved_at = datetime.now(UTC)
                    return req
        return None

    def execute(self, request_id: str) -> DeletionRequest | None:
        with self._lock:
            for req in self._requests:
                if req.id == request_id and req.status == DeletionStatus.APPROVED:
                    req.status = DeletionStatus.EXECUTED
                    req.executed_at = datetime.now(UTC)
                    return req
        return None

    def reject(self, request_id: str) -> DeletionRequest | None:
        with self._lock:
            for req in self._requests:
                if req.id == request_id and req.status == DeletionStatus.PENDING:
                    req.status = DeletionStatus.REJECTED
                    return req
        return None

    def get_by_id(self, request_id: str) -> DeletionRequest | None:
        with self._lock:
            for req in self._requests:
                if req.id == request_id:
                    return req
        return None

    def list_requests(
        self,
        subject_id: str | None = None,
        limit: int = 50,
        status: DeletionStatus | str | None = None,
    ) -> list[dict]:
        with self._lock:
            results = list(self._requests)

        if subject_id:
            results = [r for r in results if r.subject_id == subject_id]

        if status is not None:
            status_value = status.value if isinstance(status, DeletionStatus) else status
            results = [r for r in results if r.status.value == status_value]

        results.sort(key=lambda r: r.created_at, reverse=True)
        return [r.to_dict() for r in results[:limit]]

    def get_overdue(self) -> list[dict]:
        with self._lock:
            return [
                r.to_dict()
                for r in self._requests
                if r.is_overdue
            ]

    def count(self) -> int:
        with self._lock:
            return len(self._requests)

    def clear(self) -> None:
        with self._lock:
            self._requests.clear()
