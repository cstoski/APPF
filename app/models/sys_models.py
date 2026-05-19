from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Boolean,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class TimestampMixin:
    # REQUISITO 1: timestamps automáticos em ABSOLUTUTAMENTE TODAS as tabelas
    data_criacao: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    data_alteracao: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class Usuario(Base, TimestampMixin):
    __tablename__ = "usuarios"
    __table_args__ = (
        UniqueConstraint("username", name="uq_username"),
        Index("ix_usuarios_perfil", "perfil"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    perfil: Mapped[str] = mapped_column(String(20), nullable=False, default="OPERADOR")  # MASTER | OPERADOR | DEV
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ConfigAPPF(Base, TimestampMixin):
    """
    Singleton row (apenas 1 linha)
    """
    __tablename__ = "config_appf"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    razao_social: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    cnpj: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    endereco: Mapped[str] = mapped_column(String(250), nullable=False, default="")

    nome_presidente: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    caminho_assinatura_presidente: Mapped[str] = mapped_column(String(300), nullable=False, default="")

    nome_tesoureiro: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    caminho_assinatura_tesoureiro: Mapped[str] = mapped_column(String(300), nullable=False, default="")


class LicencaAtivada(Base, TimestampMixin):
    __tablename__ = "licencas_ativadas"
    __table_args__ = (
        UniqueConstraint("hwid", name="uq_hwid"),
        Index("ix_licenca_ativa", "ativa"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hwid: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    serial: Mapped[str] = mapped_column(String(100), nullable=False)
    assinatura: Mapped[str] = mapped_column(String(512), nullable=False)
    ativa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    data_ativacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class LogsAuditoriaLGPD(Base, TimestampMixin):
    """
    Logs imutáveis (nunca atualizar/deletar no código).
    """
    __tablename__ = "logs_auditoria_lgpd"
    __table_args__ = (
        Index("ix_logs_operador", "operador_username"),
        Index("ix_logs_acao", "acao"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    operador_username: Mapped[str] = mapped_column(String(80), nullable=False)

    # Ex: EXPORTACAO_CONTRIBUINTES, LEITURA_LOTE_CONTRIBUINTES, EXPORTACAO_VINCULOS
    acao: Mapped[str] = mapped_column(String(120), nullable=False)
    entidade: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    detalhes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quantidade_registros: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)