from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.all_models import User
from app.schemas.auth import UserOut
from app.services.auth import build_login_url, exchange_code_and_login

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
def login() -> RedirectResponse:
    return RedirectResponse(build_login_url())


@router.get("/callback")
async def callback(db: Annotated[Session, Depends(get_db)], code: str = Query(...)) -> RedirectResponse:
    token = await exchange_code_and_login(db, code)
    return RedirectResponse(f"{settings.app_url}/login?token={token}")


@router.post("/logout")
def logout() -> dict:
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user
