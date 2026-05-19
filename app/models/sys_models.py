from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from datetime import datetime
from . import Base


class LicencaAtivada(Base):
    __tablename__ = "licenca_ativada"
    id = Column(Integer, primary_key=True)
    hwid = Column(String(255), nullable=False)
    serial = Column(String(255), nullable=False)
    ativada_em = Column(DateTime, default=datetime.utcnow)


class ConfigAPPF(Base):
    __tablename__ = "config_appf"
    id = Column(Integer, primary_key=True)
    nome_instituicao = Column(String(255))
    assinatura_path = Column(String(1024))


class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True)
    username = Column(String(150), unique=True, index=True)
    hashed_password = Column(String(255))
    perfil = Column(String(50), default="USER")
    ativo = Column(Boolean, default=True)


class LogsAuditoriaLGPD(Base):
    __tablename__ = "logs_auditoria_lgpd"
    id = Column(Integer, primary_key=True)
    usuario = Column(String(150))
    acao = Column(String(255))
    detalhe = Column(Text)
    criado_em = Column(DateTime, default=datetime.utcnow)
