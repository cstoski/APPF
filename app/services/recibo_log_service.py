from __future__ import annotations

from datetime import datetime
from app.models.core_models import Recibo
from app.runtime_paths import get_logs_dir

LOG_DIR = get_logs_dir()
LOG_FILE = LOG_DIR / "recibos.log"

ACOES_CLIENTE = frozenset({"GERAR_PDF", "IMPRIMIR", "ENVIAR_WHATSAPP"})


def _detalhes_recibo(r: Recibo) -> str:
    partes = [f"valor={float(r.valor):.2f}"]
    if r.forma_pagamento:
        partes.append(f"forma={r.forma_pagamento}")
    if r.descricao:
        partes.append(f"desc={r.descricao[:80]}")
    if r.cancelado:
        partes.append("status=cancelado")
    return " | ".join(partes)


def registrar_log_recibo(
    operador: str,
    acao: str,
    recibo_id: int,
    numero: str,
    contribuinte_id: int,
    nome_contribuinte: str,
    detalhes: str = "",
) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha = (
        f"{ts} | operador={operador} | acao={acao} | "
        f"recibo_id={recibo_id} | numero={numero} | "
        f"contribuinte_id={contribuinte_id} | contribuinte={nome_contribuinte.strip()}"
    )
    if detalhes:
        linha += f" | {detalhes}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def log_emissao(operador: str, r: Recibo, nome_contribuinte: str) -> None:
    registrar_log_recibo(
        operador,
        "EMITIR",
        r.id,
        r.numero,
        r.contribuinte_id,
        nome_contribuinte,
        _detalhes_recibo(r),
    )


def log_cancelamento(operador: str, r: Recibo, nome_contribuinte: str, motivo: str) -> None:
    detalhes = f"{_detalhes_recibo(r)} | motivo={motivo[:200]}"
    registrar_log_recibo(
        operador,
        "CANCELAR",
        r.id,
        r.numero,
        r.contribuinte_id,
        nome_contribuinte,
        detalhes,
    )


def log_visualizacao(operador: str, r: Recibo, nome_contribuinte: str) -> None:
    registrar_log_recibo(
        operador,
        "VISUALIZAR",
        r.id,
        r.numero,
        r.contribuinte_id,
        nome_contribuinte,
        _detalhes_recibo(r),
    )


def log_enviar_email(operador: str, r: Recibo, nome_contribuinte: str, destinatario: str) -> None:
    detalhes = f"{_detalhes_recibo(r)} | email={destinatario.strip()}"
    registrar_log_recibo(
        operador,
        "ENVIAR_EMAIL",
        r.id,
        r.numero,
        r.contribuinte_id,
        nome_contribuinte,
        detalhes,
    )


def log_acao_cliente(
    operador: str,
    r: Recibo,
    nome_contribuinte: str,
    acao: str,
    detalhes: str = "",
) -> None:
    if acao not in ACOES_CLIENTE:
        raise ValueError(f"Ação de log inválida: {acao}")
    base = _detalhes_recibo(r)
    if detalhes:
        base = f"{base} | {detalhes}" if base else detalhes
    registrar_log_recibo(
        operador,
        acao,
        r.id,
        r.numero,
        r.contribuinte_id,
        nome_contribuinte,
        base,
    )
