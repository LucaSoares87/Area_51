"""
Modelos de dados para conformidade com a LGPD.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class LegalBasis(str, Enum):
    CONSENT = "consent"
    LEGITIMATE_INTEREST = "legitimate_interest"
    LEGAL_OBLIGATION = "legal_obligation"
    PUBLIC_POLICY = "public_policy"
    CONTRACT = "contract"
    VITAL_INTEREST = "vital_interest"
    CREDIT_PROTECTION = "credit_protection"
    RESEARCH = "research"
    JUDICIAL = "judicial"
    HEALTH = "health"


class DataCategory(str, Enum):
    PERSONAL = "personal"
    SENSITIVE = "sensitive"
    ANONYMOUS = "anonymous"
    PSEUDONYMIZED = "pseudonymized"
    CHILD = "child"


class PersonalDataType(str, Enum):
    FACE = "face"
    LICENSE_PLATE = "license_plate"
    GEOLOCATION = "geolocation"
    NAME = "name"
    DOCUMENT_ID = "document_id"
    BIOMETRIC = "biometric"
    IMAGE = "image"
    VIDEO = "video"
    VOICE = "voice"
    BEHAVIORAL = "behavioral"


class TreatmentOperation(str, Enum):
    COLLECTION = "collection"
    STORAGE = "storage"
    PROCESSING = "processing"
    SHARING = "sharing"
    DELETION = "deletion"
    ANONYMIZATION = "anonymization"
    TRANSFER = "transfer"
    CLASSIFICATION = "classification"
    PROFILING = "profiling"


class ConsentStatus(str, Enum):
    GRANTED = "granted"
    DENIED = "denied"
    REVOKED = "revoked"
    EXPIRED = "expired"
    PENDING = "pending"


class SubjectRequestType(str, Enum):
    ACCESS = "access"
    RECTIFICATION = "rectification"
    DELETION = "deletion"
    PORTABILITY = "portability"
    OPPOSITION = "opposition"
    REVOKE_CONSENT = "revoke_consent"
    INFORMATION = "information"
    REVIEW = "review"


class RequestStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class DeletionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    EXECUTED = "executed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class AnonymizationMethod(str, Enum):
    BLUR = "blur"
    PIXELATION = "pixelation"
    MASKING = "masking"
    HASHING = "hashing"
    GENERALIZATION = "generalization"
    SUPPRESSION = "suppression"
    NOISE_ADDITION = "noise_addition"
    K_ANONYMITY = "k_anonymity"


@dataclass
class AuditEntry:
    id: str = ""
    action: str = ""
    user: str = ""
    resource: str = ""
    detail: str = ""
    ip_address: str = ""
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "action": self.action,
            "user": self.user,
            "resource": self.resource,
            "detail": self.detail,
            "ip_address": self.ip_address,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuditEntry":
        return cls(
            id=data.get("id", ""),
            action=data.get("action", ""),
            user=data.get("user", ""),
            resource=data.get("resource", ""),
            detail=data.get("detail", ""),
            ip_address=data.get("ip_address", ""),
            timestamp=(
                datetime.fromisoformat(data["timestamp"])
                if data.get("timestamp")
                else datetime.now(timezone.utc)
            ),
            metadata=data.get("metadata", {}),
        )


@dataclass
class DataSubject:
    subject_id: str = field(default_factory=lambda: uuid4().hex)
    external_ref: str = ""
    category: DataCategory = DataCategory.PERSONAL
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "external_ref": self.external_ref,
            "category": self.category.value,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DataSubject":
        return cls(
            subject_id=data.get("subject_id", uuid4().hex),
            external_ref=data.get("external_ref", ""),
            category=DataCategory(data.get("category", "personal")),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if data.get("created_at")
                else datetime.now(timezone.utc)
            ),
            metadata=data.get("metadata", {}),
        )


@dataclass
class PersonalDataRecord:
    record_id: str = field(default_factory=lambda: uuid4().hex)
    subject_id: str = ""
    data_type: PersonalDataType = PersonalDataType.IMAGE
    category: DataCategory = DataCategory.PERSONAL
    legal_basis: LegalBasis = LegalBasis.LEGITIMATE_INTEREST
    purpose: str = ""
    storage_location: str = ""
    retention_days: int = 30
    collected_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    expires_at: datetime | None = None
    anonymized: bool = False
    anonymization_method: AnonymizationMethod | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_sensitive(self) -> bool:
        return self.category == DataCategory.SENSITIVE

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "subject_id": self.subject_id,
            "data_type": self.data_type.value,
            "category": self.category.value,
            "legal_basis": self.legal_basis.value,
            "purpose": self.purpose,
            "storage_location": self.storage_location,
            "retention_days": self.retention_days,
            "collected_at": self.collected_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "anonymized": self.anonymized,
            "anonymization_method": (
                self.anonymization_method.value if self.anonymization_method else None
            ),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PersonalDataRecord":
        return cls(
            record_id=data.get("record_id", uuid4().hex),
            subject_id=data.get("subject_id", ""),
            data_type=PersonalDataType(data.get("data_type", "image")),
            category=DataCategory(data.get("category", "personal")),
            legal_basis=LegalBasis(data.get("legal_basis", "legitimate_interest")),
            purpose=data.get("purpose", ""),
            storage_location=data.get("storage_location", ""),
            retention_days=data.get("retention_days", 30),
            collected_at=(
                datetime.fromisoformat(data["collected_at"])
                if data.get("collected_at")
                else datetime.now(timezone.utc)
            ),
            expires_at=(
                datetime.fromisoformat(data["expires_at"])
                if data.get("expires_at")
                else None
            ),
            anonymized=data.get("anonymized", False),
            anonymization_method=(
                AnonymizationMethod(data["anonymization_method"])
                if data.get("anonymization_method")
                else None
            ),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ConsentRecord:
    consent_id: str = field(default_factory=lambda: uuid4().hex)
    subject_id: str = ""
    purpose: str = ""
    legal_basis: LegalBasis = LegalBasis.CONSENT
    status: ConsentStatus = ConsentStatus.PENDING
    granted_by: str = ""
    data_types: list[PersonalDataType] = field(default_factory=list)
    granted_at: datetime | None = None
    revoked_at: datetime | None = None
    expires_at: datetime | None = None
    ip_address: str = ""
    user_agent: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def id(self) -> str:
        return self.consent_id

    @property
    def is_valid(self) -> bool:
        if self.status != ConsentStatus.GRANTED:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        return True

    def grant(self) -> None:
        self.status = ConsentStatus.GRANTED
        self.granted_at = datetime.now(timezone.utc)

    def revoke(self) -> None:
        self.status = ConsentStatus.REVOKED
        self.revoked_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        return {
            "consent_id": self.consent_id,
            "subject_id": self.subject_id,
            "purpose": self.purpose,
            "legal_basis": self.legal_basis.value,
            "status": self.status.value,
            "granted_by": self.granted_by,
            "data_types": [dt.value for dt in self.data_types],
            "granted_at": self.granted_at.isoformat() if self.granted_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConsentRecord":
        return cls(
            consent_id=data.get("consent_id", uuid4().hex),
            subject_id=data.get("subject_id", ""),
            purpose=data.get("purpose", ""),
            legal_basis=LegalBasis(data.get("legal_basis", "consent")),
            status=ConsentStatus(data.get("status", "pending")),
            granted_by=data.get("granted_by", ""),
            data_types=[
                PersonalDataType(dt) for dt in data.get("data_types", [])
            ],
            granted_at=(
                datetime.fromisoformat(data["granted_at"])
                if data.get("granted_at")
                else None
            ),
            revoked_at=(
                datetime.fromisoformat(data["revoked_at"])
                if data.get("revoked_at")
                else None
            ),
            expires_at=(
                datetime.fromisoformat(data["expires_at"])
                if data.get("expires_at")
                else None
            ),
            ip_address=data.get("ip_address", ""),
            user_agent=data.get("user_agent", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class DeletionRequest:
    id: str = field(default_factory=lambda: uuid4().hex)
    subject_id: str = ""
    reason: str = ""
    requested_by: str = ""
    status: DeletionStatus = DeletionStatus.PENDING
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    approved_at: datetime | None = None
    executed_at: datetime | None = None
    deadline_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_overdue(self) -> bool:
        if self.deadline_at is None:
            return False
        if self.status == DeletionStatus.EXECUTED:
            return False
        return datetime.now(timezone.utc) > self.deadline_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "subject_id": self.subject_id,
            "reason": self.reason,
            "requested_by": self.requested_by,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "deadline_at": self.deadline_at.isoformat() if self.deadline_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeletionRequest":
        return cls(
            id=data.get("id", uuid4().hex),
            subject_id=data.get("subject_id", ""),
            reason=data.get("reason", ""),
            requested_by=data.get("requested_by", ""),
            status=DeletionStatus(data.get("status", "pending")),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if data.get("created_at")
                else datetime.now(timezone.utc)
            ),
            approved_at=(
                datetime.fromisoformat(data["approved_at"])
                if data.get("approved_at")
                else None
            ),
            executed_at=(
                datetime.fromisoformat(data["executed_at"])
                if data.get("executed_at")
                else None
            ),
            deadline_at=(
                datetime.fromisoformat(data["deadline_at"])
                if data.get("deadline_at")
                else None
            ),
            metadata=data.get("metadata", {}),
        )


@dataclass
class SubjectRequest:
    request_id: str = field(default_factory=lambda: uuid4().hex)
    subject_id: str = ""
    request_type: SubjectRequestType = SubjectRequestType.ACCESS
    status: RequestStatus = RequestStatus.PENDING
    description: str = ""
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    deadline_at: datetime | None = None
    completed_at: datetime | None = None
    response_summary: str = ""
    handled_by: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_overdue(self) -> bool:
        if self.deadline_at is None:
            return False
        if self.status == RequestStatus.COMPLETED:
            return False
        return datetime.now(timezone.utc) > self.deadline_at

    @property
    def is_open(self) -> bool:
        return self.status in (RequestStatus.PENDING, RequestStatus.IN_PROGRESS)

    def complete(self, summary: str = "", handler: str = "") -> None:
        self.status = RequestStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.response_summary = summary
        self.handled_by = handler

    def reject(self, reason: str = "", handler: str = "") -> None:
        self.status = RequestStatus.REJECTED
        self.completed_at = datetime.now(timezone.utc)
        self.response_summary = reason
        self.handled_by = handler

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "subject_id": self.subject_id,
            "request_type": self.request_type.value,
            "status": self.status.value,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "deadline_at": self.deadline_at.isoformat() if self.deadline_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "response_summary": self.response_summary,
            "handled_by": self.handled_by,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SubjectRequest":
        return cls(
            request_id=data.get("request_id", uuid4().hex),
            subject_id=data.get("subject_id", ""),
            request_type=SubjectRequestType(data.get("request_type", "access")),
            status=RequestStatus(data.get("status", "pending")),
            description=data.get("description", ""),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if data.get("created_at")
                else datetime.now(timezone.utc)
            ),
            deadline_at=(
                datetime.fromisoformat(data["deadline_at"])
                if data.get("deadline_at")
                else None
            ),
            completed_at=(
                datetime.fromisoformat(data["completed_at"])
                if data.get("completed_at")
                else None
            ),
            response_summary=data.get("response_summary", ""),
            handled_by=data.get("handled_by", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class TreatmentRecord:
    record_id: str = field(default_factory=lambda: uuid4().hex)
    operation: TreatmentOperation = TreatmentOperation.PROCESSING
    data_type: PersonalDataType = PersonalDataType.IMAGE
    legal_basis: LegalBasis = LegalBasis.LEGITIMATE_INTEREST
    purpose: str = ""
    subject_id: str = ""
    operator: str = ""
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    details: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "operation": self.operation.value,
            "data_type": self.data_type.value,
            "legal_basis": self.legal_basis.value,
            "purpose": self.purpose,
            "subject_id": self.subject_id,
            "operator": self.operator,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TreatmentRecord":
        return cls(
            record_id=data.get("record_id", uuid4().hex),
            operation=TreatmentOperation(data.get("operation", "processing")),
            data_type=PersonalDataType(data.get("data_type", "image")),
            legal_basis=LegalBasis(data.get("legal_basis", "legitimate_interest")),
            purpose=data.get("purpose", ""),
            subject_id=data.get("subject_id", ""),
            operator=data.get("operator", ""),
            timestamp=(
                datetime.fromisoformat(data["timestamp"])
                if data.get("timestamp")
                else datetime.now(timezone.utc)
            ),
            details=data.get("details", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass
class AnonymizationRecord:
    record_id: str = field(default_factory=lambda: uuid4().hex)
    source_record_id: str = ""
    subject_id: str = ""
    data_type: PersonalDataType = PersonalDataType.IMAGE
    method: AnonymizationMethod = AnonymizationMethod.BLUR
    applied_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    reversible: bool = False
    input_ref: str = ""
    output_ref: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "source_record_id": self.source_record_id,
            "subject_id": self.subject_id,
            "data_type": self.data_type.value,
            "method": self.method.value,
            "applied_at": self.applied_at.isoformat(),
            "reversible": self.reversible,
            "input_ref": self.input_ref,
            "output_ref": self.output_ref,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AnonymizationRecord":
        return cls(
            record_id=data.get("record_id", uuid4().hex),
            source_record_id=data.get("source_record_id", ""),
            subject_id=data.get("subject_id", ""),
            data_type=PersonalDataType(data.get("data_type", "image")),
            method=AnonymizationMethod(data.get("method", "blur")),
            applied_at=(
                datetime.fromisoformat(data["applied_at"])
                if data.get("applied_at")
                else datetime.now(timezone.utc)
            ),
            reversible=data.get("reversible", False),
            input_ref=data.get("input_ref", ""),
            output_ref=data.get("output_ref", ""),
            metadata=data.get("metadata", {}),
        )
