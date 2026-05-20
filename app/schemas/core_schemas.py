from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Literal

from pydantic import BaseModel, Field, ConfigDict


ImportStatus = Literal["NOVO", "DUP_CPF", "DUP_NOME", "INVALIDO", "SEM_CONSENTIMENTO"]
ImportAcao = Literal["IMPORTAR", "ATUALIZAR", "PULAR"]


class ContribuinteCreate(BaseModel):
    nome_completo: str = Field(min_length=3, max_length=200)
    cpf: str = Field(min_length=5, max_length=20)
    email: Optional[str] = Field(default=None, max_length=200)
    telefone: Optional[str] = Field(default=None, max_length=50)
    consentimento_lgpd: bool
    observacoes: Optional[str] = Field(default=None, max_length=500)


class ContribuinteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome_completo: str
    consentimento_lgpd: bool
    data_criacao: datetime
    data_alteracao: datetime


class ContribuinteBuscaOut(BaseModel):
    id: int
    nome_completo: str
    cpf: str  # mascarado


class AlunoCreate(BaseModel):
    nome_completo: str = Field(min_length=3, max_length=200)
    turma: Optional[str] = Field(default=None, max_length=50)
    matricula: Optional[str] = Field(default=None, max_length=50)


class AlunoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome_completo: str
    turma: Optional[str]
    matricula: Optional[str]
    data_criacao: datetime
    data_alteracao: datetime


class VinculoCreate(BaseModel):
    aluno_id: int
    contribuinte_id: int
    parentesco: Optional[str] = Field(default=None, max_length=50)


class VinculoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    aluno_id: int
    contribuinte_id: int
    parentesco: Optional[str]
    data_criacao: datetime
    data_alteracao: datetime


class ReciboCreate(BaseModel):
    contribuinte_id: int
    valor: float = Field(gt=0)
    forma_pagamento: Optional[str] = Field(default=None, max_length=50)
    descricao: Optional[str] = Field(default=None, max_length=200)


class ReciboCancelamentoIn(BaseModel):
    motivo: str = Field(min_length=10, max_length=500)


class ReciboOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: str
    contribuinte_id: int
    valor: float
    data_contribuicao: datetime
    forma_pagamento: Optional[str]
    descricao: Optional[str]

    nome_presidente: str
    nome_tesoureiro: str
    caminho_assinatura_presidente: str
    caminho_assinatura_tesoureiro: str
    texto_legal_recibo: str
    usuario_emissor: str

    cancelado: bool
    motivo_cancelamento: Optional[str]
    usuario_cancelador: Optional[str]
    data_cancelamento: Optional[datetime]

    data_criacao: datetime
    data_alteracao: datetime


class EmailRelatorioIn(BaseModel):
    contribuinte_id: int
    destinatario_email: str = Field(min_length=5, max_length=200)
    assunto: str = Field(default="Histórico de Contribuições - APPF", max_length=200)


class SMTPConfigIn(BaseModel):
    host: str = Field(default="localhost", max_length=200)
    porta: int = Field(default=587, ge=1, le=65535)
    usuario: Optional[str] = Field(default=None, max_length=200)
    senha: Optional[str] = Field(default=None, max_length=200)
    usar_starttls: bool = True
    remetente: str = Field(default="nao-responder@appf.local", max_length=200)


class ImportacaoPreviewOut(BaseModel):
    total_linhas: int
    novos: int
    duplicados: int
    exemplos_duplicados: List[str]


class ImportacaoAplicarIn(BaseModel):
    """
    Para simplificar offline: o cliente envia novamente o arquivo ao aplicar.
    Em UX real, você pode manter hash e cache local.
    """
    aprovar_importacao: bool = True


class ImportacaoItemPreview(BaseModel):
    linha: int
    nome_completo: str
    cpf: str
    status: ImportStatus
    sugestao_acao: ImportAcao
    existente_id: Optional[int] = None
    existente_nome: Optional[str] = None
    existente_cpf: Optional[str] = None

class ImportacaoPreviewDetalhadoOut(BaseModel):
    total_linhas: int
    novos: int
    duplicados: int
    invalidos: int
    sem_consentimento: int
    exemplos_duplicados: List[str]
    itens: List[ImportacaoItemPreview]

class ExportacaoOut(BaseModel):
    mensagem: str