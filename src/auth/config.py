from pydantic import Field
from pydantic_settings import BaseSettings


class AuthSettings(BaseSettings):
    secret_key: str = Field("change-me-in-production", min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    api_key_prefix: str = "ahd"
    api_key_length: int = 48
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    bcrypt_rounds: int = 12
    min_password_length: int = 8
    max_login_attempts: int = 5
    lockout_minutes: int = 15

    model_config = {
        "env_prefix": "AUTH_",
        "env_file": ".env",
        "extra": "ignore",
    }


auth_settings = AuthSettings()
