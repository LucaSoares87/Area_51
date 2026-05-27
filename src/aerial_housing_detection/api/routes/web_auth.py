import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Header, HTTPException, status

from src.aerial_housing_detection.api.schemas.web_auth import (
    WebAuthLoginRequest,
    WebAuthRegisterRequest,
    WebAuthSessionResponse,
    WebAuthTokenResponse,
)

USERS_PATH = Path("data/auth/users.json")
WEB_USERS_KEY = "web_users"
ACCESS_TOKEN_TTL_MINUTES = 480
REFRESH_TOKEN_TTL_DAYS = 7

router = APIRouter(prefix="/api/v1/auth", tags=["web-auth"])


@router.post("/register", response_model=WebAuthTokenResponse)
def register(payload: WebAuthRegisterRequest) -> WebAuthTokenResponse:
    users_data = _load_users_data()
    web_users = _get_web_users(users_data)
    username = _normalize_username(payload.username)

    if username in web_users:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Usuário já cadastrado.",
        )

    now = _now_iso()
    user = {
        "username": username,
        "email": payload.email.strip().lower(),
        "full_name": payload.full_name.strip(),
        "password_hash": _hash_password(payload.password),
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }

    web_users[username] = user
    users_data[WEB_USERS_KEY] = web_users
    users_data["updated_at"] = _now_iso()
    _save_users_data(users_data)

    return _build_token_response(user)


@router.post("/login", response_model=WebAuthTokenResponse)
def login(payload: WebAuthLoginRequest) -> WebAuthTokenResponse:
    users_data = _load_users_data()
    web_users = _get_web_users(users_data)
    username = _normalize_username(payload.username)
    user = web_users.get(username)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Matrícula ou senha inválida.",
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo.",
        )

    if not _verify_password(payload.password, str(user["password_hash"])):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Matrícula ou senha inválida.",
        )

    return _build_token_response(user)


@router.get("/session", response_model=WebAuthSessionResponse)
def session(authorization: str | None = Header(default=None)) -> WebAuthSessionResponse:
    token_payload = _decode_authorization_header(authorization)

    if token_payload is None:
        return WebAuthSessionResponse(authenticated=False)

    users_data = _load_users_data()
    web_users = _get_web_users(users_data)
    user = web_users.get(str(token_payload["sub"]))

    if user is None:
        return WebAuthSessionResponse(authenticated=False)

    return WebAuthSessionResponse(
        authenticated=True,
        username=str(user["username"]),
        full_name=str(user["full_name"]),
        email=str(user["email"]),
    )


@router.post("/logout", response_model=WebAuthSessionResponse)
def logout() -> WebAuthSessionResponse:
    return WebAuthSessionResponse(authenticated=False)


def _load_users_data() -> dict[str, Any]:
    USERS_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not USERS_PATH.exists():
        data = _empty_users_data()
        _save_users_data(data)
        return data

    raw_text = USERS_PATH.read_text(encoding="utf-8-sig").strip()

    if not raw_text:
        data = _empty_users_data()
        _save_users_data(data)
        return data

    payload = json.loads(raw_text)

    if not isinstance(payload, dict):
        data = _empty_users_data()
        _save_users_data(data)
        return data

    payload.setdefault("version", 1)
    payload.setdefault("updated_at", _now_iso())

    legacy_users = payload.get("users", [])
    if not isinstance(legacy_users, list):
        legacy_users = []
    payload["users"] = legacy_users

    web_users = payload.get(WEB_USERS_KEY, {})
    if isinstance(web_users, list):
        web_users = _web_users_list_to_dict(web_users)
    if not isinstance(web_users, dict):
        web_users = {}

    payload[WEB_USERS_KEY] = web_users

    return payload


def _empty_users_data() -> dict[str, Any]:
    return {
        "version": 1,
        "updated_at": _now_iso(),
        "users": [],
        WEB_USERS_KEY: {},
    }


def _get_web_users(users_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    web_users = users_data.get(WEB_USERS_KEY, {})

    if isinstance(web_users, list):
        web_users = _web_users_list_to_dict(web_users)

    if not isinstance(web_users, dict):
        web_users = {}

    normalized_web_users = {
        _normalize_username(str(username)): user
        for username, user in web_users.items()
        if isinstance(user, dict)
    }

    users_data[WEB_USERS_KEY] = normalized_web_users
    return normalized_web_users


def _web_users_list_to_dict(web_users: list[Any]) -> dict[str, dict[str, Any]]:
    return {
        _normalize_username(str(user.get("username", ""))): user
        for user in web_users
        if isinstance(user, dict) and user.get("username")
    }


def _save_users_data(data: dict[str, Any]) -> None:
    USERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    USERS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        200_000,
    ).hex()

    return f"pbkdf2_sha256${salt}${digest}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt, digest = stored_hash.split("$", maxsplit=2)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    candidate_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        200_000,
    ).hex()

    return hmac.compare_digest(candidate_digest, digest)


def _build_token_response(user: dict[str, Any]) -> WebAuthTokenResponse:
    return WebAuthTokenResponse(
        access_token=_create_token(
            subject=str(user["username"]),
            token_type="access",
            expires_delta=timedelta(minutes=ACCESS_TOKEN_TTL_MINUTES),
        ),
        refresh_token=_create_token(
            subject=str(user["username"]),
            token_type="refresh",
            expires_delta=timedelta(days=REFRESH_TOKEN_TTL_DAYS),
        ),
        username=str(user["username"]),
        full_name=str(user["full_name"]),
        email=str(user["email"]),
    )


def _create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    issued_at = datetime.now(UTC)
    payload = {
        "sub": subject,
        "type": token_type,
        "exp": int((issued_at + expires_delta).timestamp()),
        "iat": int(issued_at.timestamp()),
        "jti": secrets.token_urlsafe(12),
    }

    encoded_payload = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return secrets.token_urlsafe(16) + "." + encoded_payload.hex()


def _decode_authorization_header(authorization: str | None) -> dict[str, Any] | None:
    if not authorization:
        return None

    prefix = "Bearer "

    if not authorization.startswith(prefix):
        return None

    token = authorization.removeprefix(prefix)

    try:
        _, payload_hex = token.split(".", maxsplit=1)
        payload = json.loads(bytes.fromhex(payload_hex).decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return None

    if int(payload.get("exp", 0)) < int(datetime.now(UTC).timestamp()):
        return None

    if payload.get("type") != "access":
        return None

    if not payload.get("sub"):
        return None

    return payload


def _normalize_username(username: str) -> str:
    return username.strip().upper()


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()
