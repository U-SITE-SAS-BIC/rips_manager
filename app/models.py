from pydantic import BaseModel
from typing import Optional


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class QueryCreate(BaseModel):
    name: str
    query_type: str
    query_text: str
    description: Optional[str] = None
