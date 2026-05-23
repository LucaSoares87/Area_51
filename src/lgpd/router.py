from fastapi import APIRouter, Depends, HTTPException, status

from src.auth.dependencies import get_current_user, require_admin
from src.auth.models import User
from src.lgpd.anonymizer import Anonymizer
from src.lgpd.audit_logger import AuditLogger
from src.lgpd.config import lgpd_settings
from src.lgpd.consent_manager import ConsentManager
from src.lgpd.data_deletion import DataDeletionService
from src.lgpd.models import DeletionStatus

router = APIRouter(prefix="/api/v1/lgpd", tags=["lgpd"])

anonymizer = Anonymizer()
audit_logger = AuditLogger()
consent_manager = ConsentManager()
deletion_service = DataDeletionService()


@router.get("/audit")
async def get_audit_logs(
    limit: int = 100,
    user_filter: str = None,
    action_filter: str = None,
    user: User = Depends(require_admin),
):
    audit_logger.log(
        action="audit.read",
        user=user.username,
        resource="audit_logs",
        detail=f"Consulta com limit={limit}",
    )
    return audit_logger.get_entries(
        limit=limit,
        user=user_filter,
        action=action_filter,
    )


@router.post("/audit/purge")
async def purge_audit(user: User = Depends(require_admin)):
    removed = audit_logger.purge_expired()
    audit_logger.log(
        action="audit.purge",
        user=user.username,
        resource="audit_logs",
        detail=f"Removidos {removed} registros expirados",
    )
    return {"removed": removed, "retention_days": lgpd_settings.audit_log_retention_days}


@router.post("/consent")
async def grant_consent(
    subject_id: str,
    purpose: str,
    user: User = Depends(get_current_user),
):
    consent = consent_manager.grant(
        subject_id=subject_id,
        purpose=purpose,
        granted_by=user.username,
    )
    audit_logger.log(
        action="consent.grant",
        user=user.username,
        resource=f"consent:{consent.id}",
        detail=f"Sujeito={subject_id}, Proposito={purpose}",
    )
    return consent


@router.post("/consent/{consent_id}/revoke")
async def revoke_consent(
    consent_id: str,
    user: User = Depends(get_current_user),
):
    consent = consent_manager.revoke(consent_id)
    if not consent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consentimento nao encontrado",
        )
    audit_logger.log(
        action="consent.revoke",
        user=user.username,
        resource=f"consent:{consent_id}",
    )
    return consent


@router.get("/consent/{subject_id}")
async def get_consents(
    subject_id: str,
    user: User = Depends(get_current_user),
):
    return consent_manager.get_by_subject(subject_id)


@router.post("/deletion")
async def request_deletion(
    subject_id: str,
    reason: str,
    user: User = Depends(get_current_user),
):
    request = deletion_service.create_request(
        subject_id=subject_id,
        reason=reason,
        requested_by=user.username,
    )
    audit_logger.log(
        action="deletion.request",
        user=user.username,
        resource=f"deletion:{request.id}",
        detail=f"Sujeito={subject_id}",
    )
    return request


@router.post("/deletion/{request_id}/approve")
async def approve_deletion(
    request_id: str,
    user: User = Depends(require_admin),
):
    request = deletion_service.approve(request_id)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitacao nao encontrada ou ja processada",
        )
    audit_logger.log(
        action="deletion.approve",
        user=user.username,
        resource=f"deletion:{request_id}",
    )
    return request


@router.post("/deletion/{request_id}/execute")
async def execute_deletion(
    request_id: str,
    user: User = Depends(require_admin),
):
    request = deletion_service.execute(request_id)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitacao nao encontrada ou nao aprovada",
        )
    audit_logger.log(
        action="deletion.execute",
        user=user.username,
        resource=f"deletion:{request_id}",
    )
    return request


@router.get("/deletion")
async def list_deletions(
    subject_id: str = None,
    limit: int = 50,
    user: User = Depends(require_admin),
):
    return deletion_service.list_requests(subject_id=subject_id, limit=limit)


@router.get("/deletion/overdue")
async def get_overdue(user: User = Depends(require_admin)):
    overdue = deletion_service.get_overdue()
    return {"count": len(overdue), "requests": overdue}


@router.post("/anonymize")
async def anonymize_data(
    records: list[dict],
    user: User = Depends(require_admin),
):
    result = anonymizer.anonymize_batch(records)
    audit_logger.log(
        action="anonymize",
        user=user.username,
        resource="records",
        detail=f"Anonimizados {len(records)} registros",
    )
    return result


@router.get("/report")
async def lgpd_report(user: User = Depends(require_admin)):
    return {
        "dpo_name": lgpd_settings.dpo_name,
        "dpo_email": lgpd_settings.dpo_email,
        "data_processor_id": lgpd_settings.data_processor_id,
        "audit_retention_days": lgpd_settings.audit_log_retention_days,
        "consent_expiry_days": lgpd_settings.consent_expiry_days,
        "deletion_max_processing_days": lgpd_settings.deletion_max_processing_days,
        "total_audit_entries": len(audit_logger.get_entries(limit=999999)),
        "active_consents": len([
            c for c in consent_manager.get_by_subject("*") if True
        ]),
        "pending_deletions": len(
            deletion_service.list_requests(status=DeletionStatus.PENDING)
        ),
    }


@router.get("/config")
async def get_lgpd_config(user: User = Depends(require_admin)):
    return {
        "audit_log_retention_days": lgpd_settings.audit_log_retention_days,
        "consent_expiry_days": lgpd_settings.consent_expiry_days,
        "deletion_grace_period_days": lgpd_settings.deletion_grace_period_days,
        "deletion_max_processing_days": lgpd_settings.deletion_max_processing_days,
        "anonymize_cpf": lgpd_settings.anonymize_cpf,
        "anonymize_name": lgpd_settings.anonymize_name,
        "anonymize_address": lgpd_settings.anonymize_address,
    }
