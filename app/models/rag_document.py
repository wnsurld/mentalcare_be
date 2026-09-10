# app/models/rag_document.py
from sqlalchemy import Column, BigInteger, Text, ARRAY
from pgvector.sqlalchemy import Vector

from app.db.base_class import Base  # 공용 Base 사용 (circular import 방지)

class RagDocument(Base):
    __tablename__ = "rag_documents"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    doc_id = Column(Text, unique=True, nullable=False)
    source_url = Column(Text)
    doc_type = Column(Text)
    text = Column(Text, nullable=False)
    emotions = Column(ARRAY(Text), default=[])
    situations = Column(ARRAY(Text), default=[])
    embedding = Column(Vector(1536))  # 실제 임베딩 차원 수에 맞게 조정
