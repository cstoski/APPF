from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.models.core_models import Contribuinte
from app.services.seguranca_service import decifrar, mascarar_cpf, normalizar_cpf

from app.runtime_paths import get_logs_dir

LOG_DIR = get_logs_dir()
LOG_FILE = LOG_DIR / "contribuintes.log"


def _detalhes_contribuinte(c: Contribuinte) -> str:
    if c.cpf_cifrado:
        cpf = mascarar_cpf(decifrar(c.cpf_cifrado) or "")
    else:
        cpf = "(sem CPF)"
    email = decifrar(c.email_cifrado) if c.email_cifrado else ""
    telefone = decifrar(c.telefone_cifrado) if c.telefone_cifrado else ""
    partes = [f"cpf={cpf}"]
    if email:
        partes.append(f"email={email}")
    if telefone:
        partes.append(f"telefone={telefone}")
    if c.observacoes:
        partes.append(f"obs={c.observacoes[:80]}")
    return " | ".join(partes)


def registrar_log_contribuinte(
    operador: str,
    acao: str,
    contribuinte_id: int,
    nome: str,
    detalhes: str = "",
) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha = (
        f"{ts} | operador={operador} | acao={acao} | "
        f"id={contribuinte_id} | nome={nome.strip()}"
    )
    if detalhes:
        linha += f" | {detalhes}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def log_inclusao(operador: str, c: Contribuinte) -> None:
    registrar_log_contribuinte(operador, "INCLUSAO", c.id, c.nome_completo, _detalhes_contribuinte(c))


def log_alteracao(operador: str, c: Contribuinte) -> None:
    registrar_log_contribuinte(operador, "ALTERACAO", c.id, c.nome_completo, _detalhes_contribuinte(c))


def log_exclusao(operador: str, c: Contribuinte) -> None:
    registrar_log_contribuinte(operador, "EXCLUSAO", c.id, c.nome_completo, _detalhes_contribuinte(c))


def log_reativacao(operador: str, c: Contribuinte) -> None:
    registrar_log_contribuinte(operador, "REATIVACAO", c.id, c.nome_completo, _detalhes_contribuinte(c))


def cpf_plain_para_validacao(c: Contribuinte) -> str | None:
    if not c.cpf_cifrado:
        return None
    norm = normalizar_cpf(decifrar(c.cpf_cifrado) or "")
    return norm or None
