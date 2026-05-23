import hashlib
import re
from typing import Any

from src.lgpd.config import lgpd_settings


class Anonymizer:
    def __init__(self) -> None:
        self._salt = lgpd_settings.anonymization_salt
        self._anonymize_cpf = lgpd_settings.anonymize_cpf
        self._anonymize_name = lgpd_settings.anonymize_name
        self._anonymize_address = lgpd_settings.anonymize_address

    def anonymize_batch(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self.anonymize_record(record) for record in records]

    def anonymize_record(self, record: dict[str, Any]) -> dict[str, Any]:
        result = dict(record)

        if self._anonymize_cpf:
            for key in ("cpf", "document_id", "documento"):
                if key in result and result[key]:
                    result[key] = self._mask_cpf(str(result[key]))

        if self._anonymize_name:
            for key in ("name", "nome", "full_name", "nome_completo"):
                if key in result and result[key]:
                    result[key] = self.hash_value(str(result[key]))

        if self._anonymize_address:
            for key in ("address", "endereco", "logradouro"):
                if key in result and result[key]:
                    result[key] = self.hash_value(str(result[key]))

        return result

    def hash_value(self, value: str) -> str:
        salted = f"{self._salt}:{value}"
        return hashlib.sha256(salted.encode("utf-8")).hexdigest()[:16]

    def mask_cpf(self, cpf: str) -> str:
        return self._mask_cpf(cpf)

    def _mask_cpf(self, cpf: str) -> str:
        digits = re.sub(r"\D", "", cpf)
        if len(digits) < 11:
            return "***.***.***-**"
        return f"***.{digits[3:6]}.***-**"
