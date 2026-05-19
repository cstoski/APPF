from pydantic import BaseModel
from typing import Optional


class ContribuicaoBase(BaseModel):
    contribuinte_id: int
    valor: str
    descricao: Optional[str] = None


class ReciboCreate(ContribuicaoBase):
    operador: Optional[str] = None


class BuscaParams(BaseModel):
    termo: Optional[str] = None
    data_inicio: Optional[str] = None
    data_fim: Optional[str] = None


class ImportacaoParams(BaseModel):
    arquivo: str


class EmailPayload(BaseModel):
    to: str
    subject: str
    body_html: str
