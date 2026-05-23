"""
Gerenciamento de API keys para autenticacao do sistema.
"""

import hashlib
import secrets
from datetime import UTC, datetime
from typing import Any

from src.auth.models import ApiKey, KeyStatus, Role


class ApiKeyStore:
    """Fachada de alto nivel para gerenciamento de API keys."""

    def __init__(self) -> None:
        self._keys: dict[str, ApiKey] = {}
        self._raw_keys: dict[str, str] = {}  # key_hash -> raw_key (apenas na criacao)

    @staticmethod
    def hash_key(raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @staticmethod
    def generate_raw_key(prefix: str = "ia", length: int = 32) -> str:
        token = secrets.token_urlsafe(length)
        return f"{prefix}_{token}"

    def create(
        self,
        owner: str,
        name: str,
        prefix: str = "ia",
        length: int = 32,
        role: Role = Role.VIEWER,
        expires_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict:
        raw_key = self.generate_raw_key(prefix=prefix, length=length)
        key_hash = self.hash_key(raw_key)

        api_key = ApiKey(
            key_hash=key_hash,
            name=name,
            role=role,
            expires_at=expires_at,
            metadata=metadata or {},
        )

        self._keys[key_hash] = api_key

        from src.auth.models import APIKeyResponse
        return APIKeyResponse(
            id=key_hash[:12],
            name=name,
            key=raw_key,
            owner=owner,
            created_at=api_key.created_at,
            is_active=True,
        )

    def validate(self, raw_key: str) -> ApiKey | None:
        key_hash = self.hash_key(raw_key)
        api_key = self._keys.get(key_hash)

        if api_key is None:
            return None

        if api_key.is_expired and api_key.status == KeyStatus.ACTIVE:
            api_key.status = KeyStatus.EXPIRED
            return None

        if not api_key.is_usable:
            return None

        api_key.last_used_at = datetime.now(UTC)
        return api_key

    def revoke(self, key_id: str, owner: str) -> bool:
        for key_hash, api_key in self._keys.items():
            if key_hash.startswith(key_id) and api_key.status == KeyStatus.ACTIVE:
                api_key.status = KeyStatus.REVOKED
                return True
        return False

    def list_by_owner(self, owner: str) -> list:
        from src.auth.models import APIKeyResponse
        results = []
        for key_hash, api_key in self._keys.items():
            if api_key.status == KeyStatus.ACTIVE:
                results.append(APIKeyResponse(
                    id=key_hash[:12],
                    name=api_key.name,
                    key=None,
                    owner=owner,
                    created_at=api_key.created_at,
                    is_active=True,
                ))
        return results

    def revoke_by_name(self, name: str) -> int:
        count = 0
        for api_key in self._keys.values():
            if api_key.name == name and api_key.status == KeyStatus.ACTIVE:
                api_key.status = KeyStatus.REVOKED
                count += 1
        return count

    def get_all(self) -> list[ApiKey]:
        return list(self._keys.values())

    def get_active(self) -> list[ApiKey]:
        return [k for k in self._keys.values() if k.is_usable]

    def get_by_role(self, role: Role) -> list[ApiKey]:
        return [k for k in self._keys.values() if k.role == role]

    def count(self) -> int:
        return len(self._keys)

    def count_active(self) -> int:
        return len(self.get_active())

    def clear(self) -> None:
        self._keys.clear()


api_key_store = ApiKeyStore()
