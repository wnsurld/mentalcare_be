from pydantic import BaseModel

class GoogleLoginRequest(BaseModel):
    credential: str  # Google ID token (JWT)

class RefreshRequest(BaseModel):
    refresh_token: str  # our JWT refresh token

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class LogoutRequest(BaseModel):
    # 선택 입력: 서버가 받은 refresh_token을 블랙리스트에 넣어 재발급 차단
    refresh_token: str | None = None
