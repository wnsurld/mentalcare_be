# Import all models here so Alembic 'autogenerate' sees them
from app.db.base_class import Base

# enums 먼저
from app.models.enum import *  # noqa

# IAM
from app.models.user import Users, OAuthIdentities, TokenRevocations  # noqa

# 채팅 세션
from app.models.chat_session import ChatSession   # noqa


# 사용자 첫 입력
from app.models.input import Inputs  # noqa

# 리포트
from app.models.reports import SessionReport, WeeklyReport  # noqa

# RAG 관련
from app.models.rag_document import RagDocument  # noqa
from app.models.routine import Routine  # noqa


