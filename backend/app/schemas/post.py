from pydantic import BaseModel
from datetime import datetime
from typing import List
from app.schemas.user import UserOut

class CommentOut(BaseModel):
    id: int
    text: str
    user: UserOut | None
    created_at: datetime
    class Config:
        orm_mode = True

class PostOut(BaseModel):
    id: int
    text: str | None
    media: str | None
    media_type: str | None
    approvals: int
    shares: int
    created_at: datetime
    user: UserOut
    comments: List[CommentOut] = []
    class Config:
        orm_mode = True