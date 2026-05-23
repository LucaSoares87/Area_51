
from fastapi import APIRouter, Depends, HTTPException, status

from src.auth.api_key_store import api_key_store
from src.auth.config import auth_settings
from src.auth.dependencies import get_current_user, require_admin
from src.auth.models import (
    APIKeyCreate,
    APIKeyResponse,
    LoginRequest,
    RegisterRequest,
    Role,
    TokenResponse,
    User,
    UserResponse,
)
from src.auth.password import hash_password, validate_password_strength, verify_password
from src.auth.store import user_store
from src.auth.tokens import create_access_token, create_refresh_token, decode_token

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(payload: RegisterRequest):
    if user_store.get_by_username(payload.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username ja cadastrado",
        )
    if user_store.get_by_email(payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email ja cadastrado",
        )

    errors = validate_password_strength(payload.password)
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=errors,
        )

    user = user_store.create(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=Role.VIEWER,
    )
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    user = user_store.get_by_username(payload.username)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desativado",
        )

    access_token = create_access_token(user.username, user.role.value)
    refresh_token = create_refresh_token(user.username, user.role.value)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=auth_settings.access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(token: str):
    payload = decode_token(token)
    if payload is None or payload.token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalido",
        )

    user = user_store.get_by_username(payload.sub)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario invalido",
        )

    access_token = create_access_token(user.username, user.role.value)
    refresh_token = create_refresh_token(user.username, user.role.value)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=auth_settings.access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/api-keys", response_model=APIKeyResponse, status_code=201)
async def create_api_key(
    payload: APIKeyCreate,
    user: User = Depends(get_current_user),
):
    key_data = api_key_store.create(
        owner=user.username,
        name=payload.name,
        prefix=auth_settings.api_key_prefix,
        length=auth_settings.api_key_length,
    )
    return key_data


@router.get("/api-keys", response_model=list[APIKeyResponse])
async def list_api_keys(user: User = Depends(get_current_user)):
    return api_key_store.list_by_owner(user.username)


@router.delete("/api-keys/{key_id}", status_code=204)
async def revoke_api_key(key_id: str, user: User = Depends(get_current_user)):
    success = api_key_store.revoke(key_id, user.username)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key nao encontrada",
        )


@router.put("/users/{username}/role", response_model=UserResponse)
async def update_role(
    username: str,
    role: Role,
    admin: User = Depends(require_admin),
):
    user = user_store.get_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario nao encontrado",
        )
    user.role = role
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )
