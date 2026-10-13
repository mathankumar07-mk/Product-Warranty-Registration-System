from typing import Annotated, Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import JWT_ALGORITHM, JWT_SECRET_KEY
from app.core.database import SessionLocal, get_db
from app.models.admin import Admin
from app.models.user import User

DBSession = Annotated[Session, Depends(get_db)]

security = HTTPBearer(auto_error=False)


def _get_token_identity(credentials: HTTPAuthorizationCredentials | None, *, admin: bool) -> int:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if not isinstance(payload, dict):
            raise ValueError("Invalid token identity")
        if payload.get("type", "access") != "access":
            raise ValueError("Invalid token type")
        subject = payload.get("sub")
        if not isinstance(subject, str) or not subject.isdecimal() or payload.get("is_admin", False) is not admin:
            raise ValueError("Invalid token identity")
        return int(subject)
    except (JWTError, ValueError) as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from error


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: DBSession,
) -> User:
    user = db.get(User, _get_token_identity(credentials, admin=False))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_current_admin(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: DBSession,
) -> Admin:
    admin = db.get(Admin, _get_token_identity(credentials, admin=True))
    if not admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin not found")
    return admin