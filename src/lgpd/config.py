from pathlib import Path

from pydantic_settings import BaseSettings


class LGPDSettings(BaseSettings):
    audit_log_retention_days: int = 1825
    consent_expiry_days: int = 365
    deletion_grace_period_days: int = 15
    deletion_max_processing_days: int = 15
    anonymization_salt: str = "change-me-in-production"
    anonymize_cpf: bool = True
    anonymize_name: bool = True
    anonymize_address: bool = True
    audit_log_dir: Path = Path("data/audit")
    report_output_dir: Path = Path("data/reports")
    dpo_email: str = ""
    dpo_name: str = ""
    data_processor_id: str = ""

    model_config = {
        "env_prefix": "LGPD_",
        "env_file": ".env",
        "extra": "ignore",
    }


lgpd_settings = LGPDSettings()
