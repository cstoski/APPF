from pydantic import BaseModel
from typing import Optional


class AuthRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UsuarioSchema(BaseModel):
    username: str
    perfil: Optional[str] = "USER"


class ConfigAPPFSchema(BaseModel):
    nome_instituicao: Optional[str]


class LicencaSchema(BaseModel):
    hwid: str
    serial: str


class LogLGPD(BaseModel):
    usuario: str
    acao: str
    detalhe: Optional[str]
