from pydantic import BaseModel, ConfigDict


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    koyun_user_id: str
    email: str | None
    username: str
    avatar: str | None
    role: str
    status: str
    daily_quota: int
    used_today: int
