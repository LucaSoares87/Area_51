from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.auth.api_key_store import api_key_store
from src.auth.models import Role, User
from src.auth.rate_limiter import RateLimiter
from src.auth.store import user_store
from src.auth.tokens import decode_token

bearer_scheme = HTTPBearer()
rate_limiter = RateLimiter()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> User:
    token = credentials.credentials

    api_key_data = api_key_store.validate(token)
    if api_key_data:
        user = user_store.get_by_username(api_key_data.owner)
        if user and user.is_active:
            return user

    payload = decode_token(token)
    if payload is None or payload.token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = user_store.get_by_username(payload.sub)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario nao encontrado",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desativado",
        )
    return user


def require_role(*roles: Role):
    async def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso restrito aos perfis: {[r.value for r in roles]}",
            )
        return user
    return checker


require_viewer = require_role(Role.VIEWER, Role.ANALYST, Role.ADMIN)
require_analyst = require_role(Role.ANALYST, Role.ADMIN)
require_admin = require_role(Role.ADMIN)
