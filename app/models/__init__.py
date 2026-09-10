"""
모든 SQLAlchemy 모델을 한 곳에서 import 하여
- Alembic autogenerate
- SQLAlchemy registry 초기화
둘 모두에 사용하기 위한 초기화 파일.
"""

# Base 클래스 (필수)
from app.db.base_class import Base

# Enum (PostgreSQL Enum 등)
from app.models.enum import (
    Provider,
    ProviderSAEnum,
    InputType,
    InputTypeSAEnum,
)

# Users / OAuth / Token
from app.models.user import (
    Users,
    OAuthIdentities,
    TokenRevocations,
)

# Chat session
from app.models.chat_session import ChatSession

# Inputs (사용자 입력)
from app.models.input import Inputs

# Reports (세션/주간 리포트)
from app.models.reports import (
    SessionReport,
    WeeklyReport,
)

# RAG 문서 / 루틴
from app.models.rag_document import RagDocument
from app.models.routine import Routine

# __all__ 선언 → IDE 자동완성과 type checker 지원
__all__ = [
    "Base",
    "Provider",
    "ProviderSAEnum",
    "InputType",
    "InputTypeSAEnum",
    "Users",
    "OAuthIdentities",
    "TokenRevocations",
    "ChatSession",
    "Inputs",
    "SessionReport",
    "WeeklyReport",
    "RagDocument",
    "Routine",
]
