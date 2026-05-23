"""
Modulo de conformidade LGPD.
"""

from src.lgpd.models import (
    AnonymizationMethod,
    AnonymizationRecord,
    AuditEntry,
    ConsentRecord,
    ConsentStatus,
    DataCategory,
    DataSubject,
    DeletionRequest,
    DeletionStatus,
    LegalBasis,
    PersonalDataRecord,
    PersonalDataType,
    RequestStatus,
    SubjectRequest,
    SubjectRequestType,
    TreatmentOperation,
    TreatmentRecord,
)

__all__ = [
    "AnonymizationMethod",
    "AnonymizationRecord",
    "AuditEntry",
    "ConsentRecord",
    "ConsentStatus",
    "DataCategory",
    "DataSubject",
    "DeletionRequest",
    "DeletionStatus",
    "LegalBasis",
    "PersonalDataRecord",
    "PersonalDataType",
    "RequestStatus",
    "SubjectRequest",
    "SubjectRequestType",
    "TreatmentOperation",
    "TreatmentRecord",
]
