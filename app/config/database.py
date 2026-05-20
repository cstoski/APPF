from __future__ import annotations

import os
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session

from app.runtime_paths import get_data_dir

DATA_DIR = get_data_dir()
DB_PATH = DATA_DIR / "appf_local.sqlite3"
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)


@event.listens_for(engine, "connect")
def _sqlite_pragmas(dbapi_connection, _connection_record) -> None:
    """Acelera leituras/gravações locais no SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=-64000")
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _migrate_contribuintes_cpf_opcional() -> None:
    """Permite CPF nulo na tabela contribuintes (SQLite)."""
    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='contribuintes'")
        ).fetchone()
        if not exists:
            return
        info = conn.execute(text("PRAGMA table_info(contribuintes)")).fetchall()
        cpf_col = next((row for row in info if row[1] == "cpf_cifrado"), None)
        if cpf_col is None or cpf_col[3] == 0:
            return

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE contribuintes_new (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    nome_completo VARCHAR(200) NOT NULL,
                    cpf_cifrado VARCHAR(512),
                    email_cifrado VARCHAR(512),
                    telefone_cifrado VARCHAR(512),
                    consentimento_lgpd BOOLEAN NOT NULL,
                    observacoes VARCHAR(500),
                    data_criacao DATETIME NOT NULL,
                    data_alteracao DATETIME NOT NULL,
                    UNIQUE (cpf_cifrado)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO contribuintes_new (
                    id, nome_completo, cpf_cifrado, email_cifrado, telefone_cifrado,
                    consentimento_lgpd, observacoes, data_criacao, data_alteracao
                )
                SELECT
                    id, nome_completo, cpf_cifrado, email_cifrado, telefone_cifrado,
                    consentimento_lgpd, observacoes, data_criacao, data_alteracao
                FROM contribuintes
                """
            )
        )
        conn.execute(text("DROP TABLE contribuintes"))
        conn.execute(text("ALTER TABLE contribuintes_new RENAME TO contribuintes"))
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_contribuintes_nome_completo "
                "ON contribuintes (nome_completo)"
            )
        )


def _migrate_contribuintes_excluido() -> None:
    """Coluna de exclusão lógica em contribuintes."""
    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='contribuintes'")
        ).fetchone()
        if not exists:
            return
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(contribuintes)")).fetchall()}
        if "excluido" in cols:
            return

    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE contribuintes "
                "ADD COLUMN excluido BOOLEAN NOT NULL DEFAULT 0"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_contribuintes_excluido "
                "ON contribuintes (excluido)"
            )
        )


def _migrate_contribuintes_busca() -> None:
    """Colunas indexadas para busca/unicidade sem descriptografar todos os registros."""
    from app.models.core_models import Contribuinte
    from app.services.contribuinte_busca_service import hash_cpf_busca, normalizar_nome_busca
    from app.services.seguranca_service import decifrar, normalizar_cpf

    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='contribuintes'")
        ).fetchone()
        if not exists:
            return
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(contribuintes)")).fetchall()}

    with engine.begin() as conn:
        if "cpf_busca_hash" not in cols:
            conn.execute(
                text("ALTER TABLE contribuintes ADD COLUMN cpf_busca_hash VARCHAR(64)")
            )
        if "nome_normalizado" not in cols:
            conn.execute(
                text("ALTER TABLE contribuintes ADD COLUMN nome_normalizado VARCHAR(200)")
            )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_contribuintes_cpf_busca_hash "
                "ON contribuintes (cpf_busca_hash)"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_contribuintes_nome_normalizado "
                "ON contribuintes (nome_normalizado)"
            )
        )

    with SessionLocal() as db:
        pendentes = db.query(Contribuinte).filter(Contribuinte.nome_normalizado.is_(None)).all()
        if not pendentes:
            return
        for c in pendentes:
            if c.cpf_cifrado and not c.cpf_busca_hash:
                cpf_norm = normalizar_cpf(decifrar(c.cpf_cifrado) or "")
                c.cpf_busca_hash = hash_cpf_busca(cpf_norm)
            if not c.nome_normalizado and c.nome_completo:
                c.nome_normalizado = normalizar_nome_busca(c.nome_completo)
        db.commit()


def _migrate_recibos_indices() -> None:
    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='recibos'")
        ).fetchone()
        if not exists:
            return
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_recibos_cancelado_data "
                "ON recibos (cancelado, data_contribuicao)"
            )
        )


def _migrate_config_appf_smtp() -> None:
    """Colunas de SMTP na configuração singleton da APPF."""
    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='config_appf'")
        ).fetchone()
        if not exists:
            return
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(config_appf)")).fetchall()}
        if "smtp_host" in cols:
            return

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE config_appf ADD COLUMN smtp_host VARCHAR(200) NOT NULL DEFAULT 'localhost'"))
        conn.execute(text("ALTER TABLE config_appf ADD COLUMN smtp_porta INTEGER NOT NULL DEFAULT 587"))
        conn.execute(text("ALTER TABLE config_appf ADD COLUMN smtp_usuario VARCHAR(200)"))
        conn.execute(text("ALTER TABLE config_appf ADD COLUMN smtp_senha_cifrada VARCHAR(500)"))
        conn.execute(
            text("ALTER TABLE config_appf ADD COLUMN smtp_usar_starttls BOOLEAN NOT NULL DEFAULT 1")
        )
        conn.execute(
            text(
                "ALTER TABLE config_appf ADD COLUMN smtp_remetente VARCHAR(200) "
                "NOT NULL DEFAULT 'nao-responder@appf.local'"
            )
        )


def _migrate_licencas_data_expiracao() -> None:
    """Prazo de validade da licença offline (datas de expiração)."""
    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='licencas_ativadas'")
        ).fetchone()
        if not exists:
            return
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(licencas_ativadas)")).fetchall()}
        if "data_expiracao" in cols:
            return

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE licencas_ativadas ADD COLUMN data_expiracao DATETIME"))
        conn.execute(
            text(
                "UPDATE licencas_ativadas SET data_expiracao = datetime(data_ativacao, '+365 days') "
                "WHERE data_expiracao IS NULL"
            )
        )


def _migrate_licencas_emissao_serial() -> None:
    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='licencas_ativadas'")
        ).fetchone()
        if not exists:
            return
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(licencas_ativadas)")).fetchall()}
        if "data_emissao_serial" in cols:
            return

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE licencas_ativadas ADD COLUMN data_emissao_serial DATETIME"))
        conn.execute(
            text(
                "UPDATE licencas_ativadas SET data_emissao_serial = data_ativacao "
                "WHERE data_emissao_serial IS NULL"
            )
        )


def _migrate_licencas_tipo_demo() -> None:
    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='licencas_ativadas'")
        ).fetchone()
        if not exists:
            return
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(licencas_ativadas)")).fetchall()}

    if "tipo_licenca" in cols and "demo_consumido" in cols:
        return

    with engine.begin() as conn:
        if "tipo_licenca" not in cols:
            conn.execute(
                text("ALTER TABLE licencas_ativadas ADD COLUMN tipo_licenca VARCHAR(20) NOT NULL DEFAULT 'PRODUCAO'")
            )
        if "demo_consumido" not in cols:
            conn.execute(
                text("ALTER TABLE licencas_ativadas ADD COLUMN demo_consumido BOOLEAN NOT NULL DEFAULT 0")
            )


def _migrate_recibos_instituicao() -> None:
    """Colunas congeladas da instituição no recibo (razão social, CNPJ, endereço)."""
    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='recibos'")
        ).fetchone()
        if not exists:
            return
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(recibos)")).fetchall()}
        if "razao_social" in cols:
            return

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE recibos ADD COLUMN razao_social VARCHAR(300) NOT NULL DEFAULT ''"))
        conn.execute(text("ALTER TABLE recibos ADD COLUMN cnpj VARCHAR(30) NOT NULL DEFAULT ''"))
        conn.execute(text("ALTER TABLE recibos ADD COLUMN endereco VARCHAR(500) NOT NULL DEFAULT ''"))
        cfg = conn.execute(
            text(
                "SELECT razao_social, cnpj, endereco FROM config_appf ORDER BY id LIMIT 1"
            )
        ).fetchone()
        if cfg:
            conn.execute(
                text(
                    "UPDATE recibos SET razao_social = :rs, cnpj = :cnpj, endereco = :end "
                    "WHERE razao_social = '' AND cnpj = '' AND endereco = ''"
                ),
                {"rs": cfg[0] or "", "cnpj": cfg[1] or "", "end": cfg[2] or ""},
            )


def _migrate_limpar_assinaturas_inexistentes() -> None:
    """Remove referências a arquivos de assinatura que não existem mais no disco."""
    from app.runtime_paths import resolver_arquivo_assinatura

    def _existe(caminho: str | None) -> bool:
        return resolver_arquivo_assinatura(caminho) is not None

    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='config_appf'")
        ).fetchone()
        if not exists:
            return
        row = conn.execute(
            text(
                "SELECT id, caminho_assinatura_presidente, caminho_assinatura_tesoureiro "
                "FROM config_appf ORDER BY id LIMIT 1"
            )
        ).fetchone()
        if not row:
            return
        cfg_id, pres, tes = row
        novo_pres = pres if _existe(pres) else ""
        novo_tes = tes if _existe(tes) else ""
        if novo_pres == (pres or "") and novo_tes == (tes or ""):
            return

    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE config_appf SET caminho_assinatura_presidente = :pres, "
                "caminho_assinatura_tesoureiro = :tes WHERE id = :id"
            ),
            {"pres": novo_pres, "tes": novo_tes, "id": cfg_id},
        )


def _drop_legacy_aluno_tables() -> None:
    """Remove tabelas de alunos/vínculos descontinuadas."""
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alunos_responsaveis"))
        conn.execute(text("DROP TABLE IF EXISTS alunos"))


def init_db() -> None:
    # Importa os modelos antes do create_all para registrar mapeamentos
    from app.models.core_models import Base as CoreBase  # noqa
    from app.models.sys_models import Base as SysBase  # noqa

    # Ambas herdam do mesmo Base (ver models/__init__.py),
    # mas importamos para garantir registro.
    from app.models import Base  # noqa

    _drop_legacy_aluno_tables()
    Base.metadata.create_all(bind=engine)
    _migrate_contribuintes_cpf_opcional()
    _migrate_contribuintes_excluido()
    _migrate_contribuintes_busca()
    _migrate_recibos_indices()
    _migrate_config_appf_smtp()
    _migrate_licencas_data_expiracao()
    _migrate_licencas_emissao_serial()
    _migrate_licencas_tipo_demo()
    _migrate_recibos_instituicao()
    from app.runtime_paths import migrar_assinaturas_legadas

    migrar_assinaturas_legadas()
    _migrate_limpar_assinaturas_inexistentes()


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