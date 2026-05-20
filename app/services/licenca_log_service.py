from __future__ import annotations

from datetime import datetime
from app.runtime_paths import get_logs_dir

LOG_DIR = get_logs_dir()
LOG_FILE = LOG_DIR / "licencas.log"


def registrar_log_licenca(
    operador: str,
    acao: str,
    hwid: str,
    *,
    serial_mascarado: str = "",
    detalhes: str = "",
) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha = f"{ts} | operador={operador.strip()} | acao={acao} | hwid={hwid.strip()}"
    if serial_mascarado:
        linha += f" | serial={serial_mascarado}"
    if detalhes:
        linha += f" | {detalhes}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def mascarar_serial(serial: str) -> str:
    s = (serial or "").strip()
    if len(s) <= 8:
        return "****"
    return s[:4] + "****" + s[-4:]
