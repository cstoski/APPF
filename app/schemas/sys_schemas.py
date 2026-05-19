from __future__ import annotations

from datetime import datetime
from typing import Optional, Literal, List

from pydantic import BaseModel, Field, ConfigDict


PerfilUsuario = Literal["MASTER", "OPERADOR", "DEV"]


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UsuarioCreate(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=6, max_length=200)
    perfil: PerfilUsuario = "OPERADOR"
    ativo: bool = True


class UsuarioUpdate(BaseModel):
    password: Optional[str] = Field(default=None, min_length=6, max_length=200)
    perfil: Optional[PerfilUsuario] = None
    ativo: Optional[bool] = None


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    perfil: str
    ativo: bool
    data_criacao: datetime
    data_alteracao: datetime


class ConfigAPPFOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    razao_social: str
    cnpj: str
    endereco: str
    nome_presidente: str
    caminho_assinatura_presidente: str
    nome_tesoureiro: str
    caminho_assinatura_tesoureiro: str
    data_criacao: datetime
    data_alteracao: datetime


class LicencaStatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ativa: bool
    hwid: str
    serial: str
    data_ativacao: datetime


class LicencaAtivarIn(BaseModel):
    serial: str = Field(min_length=3, max_length=100)


class LicencaAtivarOut(BaseModel):
    ativa: bool
    mensagem: str


class LogLGPDOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    operador_username: str
    acao: str
    entidade: str
    detalhes: Optional[str]
    quantidade_registros: Optional[int]
    data_criacao: datetime
    data_alteracao: datetime