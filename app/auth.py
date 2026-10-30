from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import User, Workspace
from .security import decode_access_token

JWT_COOKIE_NAME = "bioworkspace_token"


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(JWT_COOKIE_NAME, "")
    authorization = request.headers.get("authorization", "")
    if not token and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    claims = decode_access_token(token) if token else None
    if claims:
        user = db.get(User, int(claims["sub"]))
        if user:
            return user
    if settings.app_env == "test" and settings.dev_auth:
        email = request.headers.get("x-dev-user", "").strip().lower()
        if "@" in email:
            user = db.scalar(select(User).where(User.email == email))
            if not user:
                user = User(email=email, display_name=email.split("@", 1)[0], role="student")
                db.add(user)
                db.flush()
                db.add(Workspace(owner_id=user.id))
                db.commit()
                db.refresh(user)
            return user
    raise HTTPException(401, "Sign in to continue")


def optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    try:
        return current_user(request, db)
    except HTTPException:
        return None


def get_default_workspace(db: Session, user: User) -> Workspace:
    workspace = db.scalar(select(Workspace).where(Workspace.owner_id == user.id).order_by(Workspace.id))
    if not workspace:
        workspace = Workspace(owner_id=user.id)
        db.add(workspace)
        db.commit()
        db.refresh(workspace)
    return workspace
