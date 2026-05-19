from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from . import Base

# Association table for N:N Alunos <-> Responsaveis
alunos_responsaveis = Table(
    "alunos_responsaveis",
    Base.metadata,
    Column("aluno_id", Integer, ForeignKey("alunos.id"), primary_key=True),
    Column("responsavel_id", Integer, ForeignKey("contribuintes.id"), primary_key=True),
)


class Contribuinte(Base):
    __tablename__ = "contribuintes"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    cpf_cnpj = Column(String(64), nullable=True)
    email = Column(String(255), nullable=True)


class Aluno(Base):
    __tablename__ = "alunos"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    vinculos = relationship("Contribuinte", secondary=alunos_responsaveis)


class Recibo(Base):
    __tablename__ = "recibos"
    id = Column(Integer, primary_key=True, index=True)
    contribuinte_id = Column(Integer, ForeignKey("contribuintes.id"), nullable=False)
    valor = Column(String(64))
    descricao = Column(Text)
    operador = Column(String(100))
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
