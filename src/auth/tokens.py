from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from src.auth.config import auth_settings
from src.auth.models import TokenPayload


def create_access_token(
    subject: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        or timedelta(minutes=auth_settings.access_token_expire_minutes)
    )
    payload = {
        "sub": subject,
        "role": role,
        "type": "access",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(
        payload,
        auth_settings.secret_key,
        algorithm=auth_settings.algorithm,
    )


def create_refresh_token(subject: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=auth_settings.refresh_token_expire_days)
    payload = {
        "sub": subject,
        "role": role,
        "type": "refresh",
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(
        payload,
        auth_settings.secret_key,
        algorithm=auth_settings.algorithm,
    )


def decode_token(token: str) -> Optional[TokenPayload]:
    try:
        data = jwt.decode(
            token,
            auth_settings.secret_key,
            algorithms=[auth_settings.algorithm],
        )
        return TokenPayload(
            sub=data["sub"],
            role=data.get("role", "viewer"),
            token_type=data.get("type", "access"),
            exp=data.get("exp"),
        )
    except JWTError:
        return None
