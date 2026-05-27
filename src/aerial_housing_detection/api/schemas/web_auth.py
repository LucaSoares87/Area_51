from pydantic import BaseModel, Field


class WebAuthRegisterRequest(BaseModel):
    username: str = Field(..., min_length=1)
    email: str = Field(..., min_length=3)
    full_name: str = Field(..., min_length=1)
    password: str = Field(..., min_length=6)


class WebAuthLoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class WebAuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    username: str
    full_name: str
    email: str


class WebAuthSessionResponse(BaseModel):
    authenticated: bool
    username: str | None = None
    full_name: str | None = None
    email: str | None = None
