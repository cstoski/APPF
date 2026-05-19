from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Caminho local (offline)
BASE_DIR = Path(__file__).resolve().parents[1]  # app/
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "appf_local.sqlite3"
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Importa os modelos antes do create_all para registrar mapeamentos
    from app.models.core_models import Base as CoreBase  # noqa
    from app.models.sys_models import Base as SysBase  # noqa

    # Ambas herdam do mesmo Base (ver models/__init__.py),
    # mas importamos para garantir registro.
    from app.models import Base  # noqa

    Base.metadata.create_all(bind=engine)


def seed_admin_if_needed() -> None:
    """
    Cria o usuário MASTER padrão se a tabela estiver vazia.
    Requisito: ("admin" / "admin_password_appf")
    """
    from app.models.sys_models import Usuario
    from app.services.seguranca_service import hash_senha

    with SessionLocal() as db:
        total = db.query(Usuario).count()
        if total == 0:
            admin = Usuario(
                username="admin",
                senha_hash=hash_senha("admin_password_appf"),
                perfil="MASTER",
                ativo=True,
            )
            db.add(admin)
            db.commit()


def ensure_singleton_config_appf() -> None:
    """
    Garante que exista 1 linha de ConfigAPPF (singleton row).
    """
    from app.models.sys_models import ConfigAPPF

    with SessionLocal() as db:
        cfg = db.query(ConfigAPPF).first()
        if cfg is None:
            cfg = ConfigAPPF(
                razao_social="",
                cnpj="",
                endereco="",
                nome_presidente="",
                caminho_assinatura_presidente="",
                nome_tesoureiro="",
                caminho_assinatura_tesoureiro="",
            )
            db.add(cfg)
            db.commit()