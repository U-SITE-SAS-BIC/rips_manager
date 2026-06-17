from pydantic import BaseModel
from typing import Optional


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class ConfigUpdate(BaseModel):
    key: str
    value: str


class QueryCreate(BaseModel):
    name: str
    query_type: str
    query_text: str
    description: Optional[str] = None


class QueryUpdate(BaseModel):
    name: Optional[str] = None
    query_text: Optional[str] = None
    description: Optional[str] = None


class SendRequest(BaseModel):
    tipo: str
    fecha_inicio: str
    fecha_fin: str
    factura: Optional[str] = None
