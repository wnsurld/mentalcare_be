# app/models/routine.py
from sqlalchemy import Column, Text, Integer, BigInteger
from sqlalchemy.dialects.postgresql import ARRAY
from pgvector.sqlalchemy import Vector

from app.db.base_class import Base


class Routine(Base):
    __tablename__ = "routines"

    # JSONL / 논리 ID (텍스트 슬러그)
    routine_id = Column(Text, primary_key=True)

    source_doc_id = Column(Text, nullable=True)
    source_url = Column(Text, nullable=True)

    title = Column(Text, nullable=False)
    goal = Column(Text, nullable=True)
    description = Column(Text, nullable=True)

    target_emotions = Column(ARRAY(Text), nullable=False, server_default="{}")
    target_situations = Column(ARRAY(Text), nullable=False, server_default="{}")

    routine_type = Column(Text, nullable=True)
    difficulty = Column(Text, nullable=True)
    duration_min = Column(Integer, nullable=True)

    environment = Column(ARRAY(Text), nullable=False, server_default="{}")
    required_tools = Column(ARRAY(Text), nullable=False, server_default="{}")

    steps = Column(ARRAY(Text), nullable=False, server_default="{}")
    safety_notes = Column(ARRAY(Text), nullable=False, server_default="{}")

    tags = Column(ARRAY(Text), nullable=False, server_default="{}")
    language = Column(Text, nullable=False, server_default="ko")

    embedding = Column(Vector(768), nullable=True)
