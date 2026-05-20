from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Boolean,
    ForeignKey,
    Numeric,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class TimestampMixin:
    # REQUISITO 1: timestamps automáticos em ABSOLUTAMENTE TODAS as tabelas
    data_criacao: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    data_alteracao: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class Contribuinte(Base, TimestampMixin):
    __tablename__ = "contribuintes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    nome_completo: Mapped[str] = mapped_column(String(200), nullable=False, index=True)

    # Dados sensíveis cifrados (LGPD)
    cpf_cifrado: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, unique=True)
    email_cifrado: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    telefone_cifrado: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    consentimento_lgpd: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    observacoes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    excluido: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    # Índices de busca/unicidade sem descriptografar o lote inteiro
    cpf_busca_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    nome_normalizado: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)

    recibos: Mapped[List["Recibo"]] = relationship(
        back_populates="contribuinte", cascade="save-update"
    )


class Recibo(Base, TimestampMixin):
    __tablename__ = "recibos"
    __table_args__ = (
        UniqueConstraint("numero", name="uq_numero_recibo"),
        Index("ix_recibos_contribuinte_data", "contribuinte_id", "data_contribuicao"),
        Index("ix_recibos_cancelado_data", "cancelado", "data_contribuicao"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Numeração imutável AAAAMMDD + contador diário de 4 dígitos
    numero: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)

    contribuinte_id: Mapped[int] = mapped_column(ForeignKey("contribuintes.id"), nullable=False)
    contribuinte: Mapped["Contribuinte"] = relationship(back_populates="recibos")

    valor: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    data_contribuicao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    forma_pagamento: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    descricao: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Congelamento histórico da instituição e gestão
    razao_social: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    cnpj: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    endereco: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    nome_presidente: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    nome_tesoureiro: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    caminho_assinatura_presidente: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    caminho_assinatura_tesoureiro: Mapped[str] = mapped_column(String(300), nullable=False, default="")

    # Texto legal gerado dinamicamente (sem termos proibidos)
    texto_legal_recibo: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Auditoria do operador
    usuario_emissor: Mapped[str] = mapped_column(String(80), nullable=False, default="")

    # Cancelamento lógico
    cancelado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    motivo_cancelamento: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    usuario_cancelador: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    data_cancelamento: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)