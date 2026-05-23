from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, EmailStr


class Role(str, Enum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    ADMIN = "admin"


class KeyStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


class TokenType(str, Enum):
    BEARER = "bearer"
    SERVICE = "service"
    TEMPORARY = "temporary"


@dataclass
class User:
    id: str = field(default_factory=lambda: str(uuid4()))
    username: str = ""
    email: str = ""
    full_name: str = ""
    hashed_password: str = ""
    role: Role = Role.VIEWER
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "hashed_password": self.hashed_password,
            "role": self.role.value,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "User":
        return cls(
            id=data.get("id", str(uuid4())),
            username=data.get("username", ""),
            email=data.get("email", ""),
            full_name=data.get("full_name", ""),
            hashed_password=data.get("hashed_password", ""),
            role=Role(data.get("role", "viewer")),
            is_active=data.get("is_active", True),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if "created_at" in data
                else datetime.now(UTC)
            ),
        )


@dataclass
class ApiKey:
    key_hash: str = ""
    name: str = ""
    role: Role = Role.VIEWER
    status: KeyStatus = KeyStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(UTC) > self.expires_at

    @property
    def is_usable(self) -> bool:
        return self.status == KeyStatus.ACTIVE and not self.is_expired

    def to_dict(self) -> dict[str, Any]:
        return {
            "key_hash": self.key_hash,
            "name": self.name,
            "role": self.role.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ApiKey":
        return cls(
            key_hash=data.get("key_hash", ""),
            name=data.get("name", ""),
            role=Role(data.get("role", "viewer")),
            status=KeyStatus(data.get("status", "active")),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if "created_at" in data
                else datetime.now(UTC)
            ),
            expires_at=(
                datetime.fromisoformat(data["expires_at"])
                if data.get("expires_at")
                else None
            ),
            last_used_at=(
                datetime.fromisoformat(data["last_used_at"])
                if data.get("last_used_at")
                else None
            ),
            metadata=data.get("metadata", {}),
        )


@dataclass
class AuthResult:
    authenticated: bool = False
    api_key: ApiKey | None = None
    reason: str = ""


@dataclass
class RateLimitEntry:
    key_hash: str = ""
    window_start: datetime = field(default_factory=lambda: datetime.now(UTC))
    request_count: int = 0
    max_requests: int = 100
    window_seconds: int = 3600

    @property
    def is_limited(self) -> bool:
        if self.is_window_expired:
            return False
        return self.request_count >= self.max_requests

    @property
    def is_window_expired(self) -> bool:
        elapsed = (datetime.now(UTC) - self.window_start).total_seconds()
        return elapsed >= self.window_seconds

    def increment(self) -> None:
        if self.is_window_expired:
            self.window_start = datetime.now(UTC)
            self.request_count = 0
        self.request_count += 1


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenPayload(BaseModel):
    sub: str
    role: str = "viewer"
    token_type: str = "access"
    exp: int | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: Role
    is_active: bool
    created_at: datetime


class APIKeyCreate(BaseModel):
    name: str


class APIKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = ""
    name: str = ""
    key: str | None = None
    owner: str = ""
    created_at: datetime | None = None
    is_active: bool = True
