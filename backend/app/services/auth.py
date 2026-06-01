from datetime import UTC, datetime
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import UserRole
from app.models.all_models import User
from app.services.admins import parse_admin_emails
from app.utils.security import create_access_token


def build_login_url(state: str | None = None) -> str:
    if not settings.koyun_oauth_authorize_url:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="OAuth authorize URL is not configured")
    params = {
        "client_id": settings.koyun_oauth_client_id,
        "redirect_uri": settings.koyun_oauth_redirect_uri,
        "response_type": "code",
        "scope": "openid profile email",
    }
    if state:
        params["state"] = state
    return f"{settings.koyun_oauth_authorize_url}?{urlencode(params)}"


async def exchange_code_and_login(db: Session, code: str) -> str:
    if not settings.koyun_oauth_token_url or not settings.koyun_oauth_userinfo_url:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="OAuth token or userinfo URL is not configured")

    async with httpx.AsyncClient(timeout=20) as client:
        token_resp = await client.post(
            settings.koyun_oauth_token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.koyun_oauth_client_id,
                "client_secret": settings.koyun_oauth_client_secret,
                "redirect_uri": settings.koyun_oauth_redirect_uri,
            },
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "curl/8.5.0",
            },
        )
        if token_resp.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"OAuth token failed: {token_resp.status_code} {token_resp.text[:800]}",
            )
        access_token = token_resp.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="OAuth token response did not include access_token")

        user_resp = await client.get(
            settings.koyun_oauth_userinfo_url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "User-Agent": "curl/8.5.0",
            },
        )
        if user_resp.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"OAuth userinfo failed: {user_resp.status_code} {user_resp.text[:800]}",
            )
        profile = normalize_koyun_profile(user_resp.json())

    user = upsert_user(db, profile)
    db.commit()
    return create_access_token(str(user.id), user.role)


def normalize_koyun_profile(payload: dict) -> dict:
    koyun_id = payload.get("id") or payload.get("sub") or payload.get("user_id")
    if not koyun_id:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Koyun userinfo did not include a user id")
    return {
        "koyun_user_id": str(koyun_id),
        "email": payload.get("email") or payload.get("mail"),
        "username": payload.get("name") or payload.get("username") or payload.get("nickname") or f"koyun-{koyun_id}",
        "avatar": payload.get("avatar") or payload.get("picture"),
        "role": payload.get("role"),
    }


def upsert_user(db: Session, profile: dict) -> User:
    user = db.query(User).filter(User.koyun_user_id == profile["koyun_user_id"]).first()
    role = profile.get("role") if profile.get("role") in {UserRole.USER, UserRole.VIP, UserRole.ADMIN} else None
    email = (profile.get("email") or "").lower()
    if email and email in parse_admin_emails():
        role = UserRole.ADMIN
    if user:
        user.email = profile["email"]
        user.username = profile["username"]
        user.avatar = profile["avatar"]
        if role:
            user.role = role
        user.last_login_at = datetime.now(UTC)
        return user

    user = User(
        koyun_user_id=profile["koyun_user_id"],
        email=profile["email"],
        username=profile["username"],
        avatar=profile["avatar"],
        role=role or UserRole.USER,
        daily_quota=50 if role == UserRole.VIP else 5,
        last_login_at=datetime.now(UTC),
    )
    db.add(user)
    db.flush()
    return user
