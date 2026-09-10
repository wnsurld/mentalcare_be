# app/core/config.py

from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AliasChoices, field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True,
    )

    # ---- 앱 메타 ----
    APP_NAME: str = Field("MentalCare BE", description="Application name")
    APP_ENV: Literal["development", "staging", "production"] = Field(
        "development", description="App environment"
    )

    # ---- DB ----
    DATABASE_URL: str = Field(..., description="SQLAlchemy URL")

    # ---- JWT/보안 ----
    JWT_ALG: str = Field(
        "HS256",
        description="JWT signing algorithm",
        validation_alias=AliasChoices("JWT_ALG", "JWT_ALGORITHM"),
    )
    JWT_SECRET: str = Field(..., description="JWT signing secret")

    ACCESS_TOKEN_MIN: int = Field(30, description="Access token lifetime (minutes)")
    REFRESH_TOKEN_DAYS: int = Field(7, description="Refresh token lifetime (days)")

    # ---- OAuth ----
    GOOGLE_CLIENT_ID: str = Field(..., description="Google OAuth Web Client ID")

    REDIS_URL: str

    @property
    def is_dev(self) -> bool:
        return self.APP_ENV == "development"

    # JWT_ALGORITHM 호환용
    @property
    def JWT_ALGORITHM(self) -> str:
        return self.JWT_ALG

    @field_validator("DATABASE_URL")
    @classmethod
    def _validate_db_url(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("DATABASE_URL is empty")
        if v.startswith("postgres://"):
            v = "postgresql+psycopg2://" + v[len("postgres://") :]
        if not (v.startswith("postgresql://") or v.startswith("postgresql+")):
            raise ValueError(
                "DATABASE_URL must start with 'postgresql+psycopg2://' (or 'postgresql://')"
            )
        return v


settings = Settings()
