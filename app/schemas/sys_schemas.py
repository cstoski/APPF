from __future__ import annotations

from datetime import date, datetime
from typing import Optional, Literal, List

from pydantic import BaseModel, Field, ConfigDict


PerfilUsuario = Literal["MASTER", "OPERADOR", "DEV"]


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TrocarSenhaPropriaIn(BaseModel):
    senha_atual: str = Field(min_length=1, max_length=200)
    nova_senha: str = Field(min_length=6, max_length=200)


class UsuarioCreate(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=6, max_length=200)
    perfil: PerfilUsuario = "OPERADOR"
    ativo: bool = True


class UsuarioUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=80)
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
    smtp_host: str
    smtp_porta: int
    smtp_usuario: Optional[str] = None
    smtp_senha_configurada: bool = False
    smtp_usar_starttls: bool = True
    smtp_remetente: str
    data_criacao: datetime
    data_alteracao: datetime


class ValidacaoConfigItemOut(BaseModel):
    campo: str
    ok: bool
    mensagem: str


class ConfigValidacaoOut(BaseModel):
    ok: bool
    escopo: str
    itens: list[ValidacaoConfigItemOut]


class ConfigSalvarOut(BaseModel):
    config: ConfigAPPFOut
    validacao: ConfigValidacaoOut


class LicencaStatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ativa: bool
    registrada: bool
    expirada: bool
    integridade_ok: bool
    hwid: str
    serial: str
    data_ativacao: Optional[datetime] = None
    data_expiracao: Optional[datetime] = None
    data_emissao_serial: Optional[date] = None
    dias_restantes: Optional[int] = None
    grace_dias_restantes: Optional[int] = None
    validade_dias: int = 365
    grace_dias: int = 7
    modo: str = "NAO_ATIVADA"
    pode_leitura: bool = False
    pode_escrita: bool = False
    aviso_expiracao: bool = False
    tipo_licenca: str = "PRODUCAO"
    eh_demo: bool = False
    demo_consumido: bool = False
    serial_demo: str = "DEMO-APPF-DEMO-3DAY"


class LicencaAtivarIn(BaseModel):
    serial: str = Field(min_length=11, max_length=100)


class LicencaAtivarOut(BaseModel):
    ativa: bool
    mensagem: str
    data_ativacao: Optional[datetime] = None
    data_expiracao: Optional[datetime] = None


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