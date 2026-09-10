from pydantic import BaseModel, Field
from typing import List, Dict, Any


class RetrieveRequest(BaseModel):
    input_text: str = Field(..., description="사용자 입력 텍스트")
    top_k: int = 5


class Doc(BaseModel):
    doc_id: str
    title: str
    snippet: str
    score: float


class RetrieveResponse(BaseModel):
    query: str
    filters: Dict[str, Any] = {}
    docs: List[Doc]