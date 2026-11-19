from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    top_k: int = Field(default=4, ge=1, le=10)

class Citation(BaseModel):
    document_id: str
    filename: str
    chunk_id: int
    page: int | None = None
    excerpt: str
    score: float

class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
