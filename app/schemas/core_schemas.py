from __future__ import annotations

from datetime import date, datetime
from typing import Optional, List, Literal

from pydantic import BaseModel, Field, ConfigDict


ImportStatus = Literal["NOVO", "DUP_CPF", "DUP_NOME", "INVALIDO", "SEM_CONSENTIMENTO"]
ImportAcao = Literal["IMPORTAR", "ATUALIZAR", "PULAR"]


class ContribuinteCreate(BaseModel):
    nome_completo: str = Field(min_length=3, max_length=200)
    cpf: Optional[str] = Field(default=None, max_length=20)
    email: Optional[str] = Field(default=None, max_length=200)
    telefone: Optional[str] = Field(default=None, max_length=50)
    consentimento_lgpd: bool = True
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
    email: Optional[str] = None
    telefone: Optional[str] = None
    excluido: bool = False


class ContribuinteUpdate(BaseModel):
    nome_completo: str = Field(min_length=3, max_length=200)
    cpf: Optional[str] = Field(default=None, max_length=20)
    email: Optional[str] = Field(default=None, max_length=200)
    telefone: Optional[str] = Field(default=None, max_length=50)
    observacoes: Optional[str] = Field(default=None, max_length=500)


class ContribuinteDetalheOut(BaseModel):
    id: int
    nome_completo: str
    cpf: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    observacoes: Optional[str] = None


class ReciboCreate(BaseModel):
    contribuinte_id: int
    valor: float = Field(gt=0)
    data_contribuicao: date
    forma_pagamento: Optional[str] = Field(default=None, max_length=50)
    descricao: Optional[str] = Field(default=None, max_length=200)


class ReciboCancelamentoIn(BaseModel):
    motivo: str = Field(min_length=10, max_length=500)


class ReciboListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: str
    valor: float
    data_contribuicao: datetime
    forma_pagamento: Optional[str] = None
    descricao: Optional[str] = None
    cancelado: bool
    motivo_cancelamento: Optional[str] = None


class ReciboOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: str
    contribuinte_id: int
    valor: float
    data_contribuicao: datetime
    forma_pagamento: Optional[str]
    descricao: Optional[str]

    razao_social: str
    cnpj: str
    endereco: str
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


class RelatorioLinhaOut(BaseModel):
    id: int
    numero: str
    data_contribuicao: datetime
    valor: float
    forma_pagamento: Optional[str] = None
    descricao: Optional[str] = None
    cancelado: bool = False
    contribuinte_id: Optional[int] = None
    contribuinte_nome: Optional[str] = None


class RelatorioResumoOut(BaseModel):
    quantidade: int
    valor_total: float
    valor_medio: float
    quantidade_cancelados: int = 0


class RelatorioInstituicaoOut(BaseModel):
    razao_social: str
    cnpj: str
    nome_presidente: str = ""
    nome_tesoureiro: str = ""
    caminho_assinatura_presidente: str = ""
    caminho_assinatura_tesoureiro: str = ""


class RelatorioContribuinteOut(BaseModel):
    titulo: str
    contribuinte_id: int
    contribuinte_nome: str
    contribuinte_cpf: Optional[str] = None
    periodo_label: str
    data_inicio: datetime
    data_fim: datetime
    instituicao: RelatorioInstituicaoOut
    linhas: List[RelatorioLinhaOut]
    resumo: RelatorioResumoOut


class RelatorioMesTotalOut(BaseModel):
    mes: int
    mes_label: str
    quantidade: int
    valor_total: float


class RelatorioFinanceiroOut(BaseModel):
    titulo: str
    periodo: Literal["mensal", "semestral", "anual"]
    periodo_label: str
    data_inicio: datetime
    data_fim: datetime
    instituicao: RelatorioInstituicaoOut
    linhas: List[RelatorioLinhaOut]
    resumo: RelatorioResumoOut
    totais_mensais: Optional[List[RelatorioMesTotalOut]] = None


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


class ReciboLogAcaoIn(BaseModel):
    acao: str = Field(min_length=3, max_length=50)
    detalhes: Optional[str] = Field(default=None, max_length=500)


class ReciboEmailIn(BaseModel):
    destinatario_email: str = Field(min_length=5, max_length=200)
    assunto: str = Field(min_length=3, max_length=200)
    corpo_texto: str = Field(min_length=10, max_length=8000)
    pdf_base64: str = Field(min_length=100)
    nome_anexo: str = Field(default="recibo.pdf", min_length=4, max_length=255)


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