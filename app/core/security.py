# app/core/security.py
from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import Users

# ------------------------------------------------------------
# JWT 관련 기본 세팅
# ------------------------------------------------------------

# 🔥 여기 변경됨
bearer_scheme = HTTPBearer(auto_error=True)

def _now_utc() -> datetime:
    return datetime.utcnow()


# ------------------------------------------------------------
# 토큰 생성 로직 (access / refresh)
# ------------------------------------------------------------

def create_access_token(user_claims: Dict[str, Any]) -> str:
    now = _now_utc()
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_MIN)

    payload = {
        "iss": settings.APP_NAME,
        "typ": "access",
        "usr": user_claims,
        "iat": now.timestamp(),
        "exp": expire.timestamp(),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_claims: Dict[str, Any]) -> str:
    now = _now_utc()
    expire = now + timedelta(days=settings.REFRESH_TOKEN_DAYS)

    payload = {
        "iss": settings.APP_NAME,
        "typ": "refresh",
        "usr": user_claims,
        "iat": now.timestamp(),
        "exp": expire.timestamp(),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


# ------------------------------------------------------------
# 공통 디코더
# ------------------------------------------------------------

def decode_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_aud": False},
        )
        print("🔐 decode_token payload =", payload)
        return payload

    except JWTError as e:
        print("❌ decode_token JWTError:", repr(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token (decode_failed)",
        ) from e

def get_user_from_claims(db: Session, claims: Dict[str, Any]) -> Users:
    usr = claims.get("usr") or {}
    user_id_raw = usr.get("sub")

    if not user_id_raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user = db.query(Users).filter(Users.id == user_id_raw).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user

# ------------------------------------------------------------
# 현재 유저 가져오기
# ------------------------------------------------------------

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Users:
    """
    HTTPBearer → "Bearer <token>" 형식에서 token만 추출됨
    """
    token = credentials.credentials  # ← 핵심
    print("🔐 get_current_user token prefix:", token[:30])

    payload = decode_token(token)

    if payload.get("typ") != "access":
        raise HTTPException(status_code=401, detail="Invalid token (wrong_typ)")

    return get_user_from_claims(db, payload)
