from __future__ import annotations

from datetime import datetime
from app.runtime_paths import get_logs_dir

LOG_DIR = get_logs_dir()
LOG_FILE = LOG_DIR / "emails.log"

# Status do envio (o que o sistema consegue medir via SMTP)
STATUS_ENFILEIRADO = "ENFILEIRADO"
STATUS_ACEITO_SMTP = "ACEITO_SMTP"
STATUS_FALHA = "FALHA"
STATUS_TESTE_SMTP = "TESTE_SMTP"

# Entrega/leitura: SMTP simples não confirma caixa de entrada nem abertura
ENTREGA_NAO_RASTREADO = "nao_rastreado"
ENTREGA_ACEITO_SERVIDOR = "aceito_pelo_servidor_smtp"
LEITURA_NAO_RASTREADO = "nao_rastreado"


def _truncar(texto: str, limite: int = 300) -> str:
    t = (texto or "").replace("\n", " ").replace("\r", " ").strip()
    if len(t) <= limite:
        return t
    return t[: limite - 3] + "..."


def registrar_log_email(
    operador: str,
    status: str,
    tipo: str,
    destinatario: str,
    *,
    remetente: str = "",
    assunto: str = "",
    recibo_id: int | None = None,
    recibo_numero: str = "",
    contribuinte_id: int | None = None,
    contribuinte_nome: str = "",
    erro: str = "",
    entrega: str = ENTREGA_NAO_RASTREADO,
    leitura: str = LEITURA_NAO_RASTREADO,
    smtp_host: str = "",
) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    partes = [
        f"{ts}",
        f"operador={_truncar(operador, 80)}",
        f"status={status}",
        f"tipo={tipo}",
        f"destinatario={_truncar(destinatario, 120)}",
    ]
    if remetente:
        partes.append(f"remetente={_truncar(remetente, 120)}")
    if assunto:
        partes.append(f"assunto={_truncar(assunto, 160)}")
    if recibo_id is not None:
        partes.append(f"recibo_id={recibo_id}")
    if recibo_numero:
        partes.append(f"recibo_numero={_truncar(recibo_numero, 40)}")
    if contribuinte_id is not None:
        partes.append(f"contribuinte_id={contribuinte_id}")
    if contribuinte_nome:
        partes.append(f"contribuinte={_truncar(contribuinte_nome, 120)}")
    partes.append(f"entrega={entrega}")
    partes.append(f"leitura={leitura}")
    if smtp_host:
        partes.append(f"smtp_host={_truncar(smtp_host, 80)}")
    if erro:
        partes.append(f"erro={_truncar(erro, 400)}")

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(" | ".join(partes) + "\n")


def log_email_enfileirado(
    operador: str,
    tipo: str,
    destinatario: str,
    *,
    remetente: str = "",
    assunto: str = "",
    recibo_id: int | None = None,
    recibo_numero: str = "",
    contribuinte_id: int | None = None,
    contribuinte_nome: str = "",
    smtp_host: str = "",
) -> None:
    registrar_log_email(
        operador,
        STATUS_ENFILEIRADO,
        tipo,
        destinatario,
        remetente=remetente,
        assunto=assunto,
        recibo_id=recibo_id,
        recibo_numero=recibo_numero,
        contribuinte_id=contribuinte_id,
        contribuinte_nome=contribuinte_nome,
        entrega=ENTREGA_NAO_RASTREADO,
        leitura=LEITURA_NAO_RASTREADO,
        smtp_host=smtp_host,
    )


def log_email_aceito_smtp(
    operador: str,
    tipo: str,
    destinatario: str,
    *,
    remetente: str = "",
    assunto: str = "",
    recibo_id: int | None = None,
    recibo_numero: str = "",
    contribuinte_id: int | None = None,
    contribuinte_nome: str = "",
    smtp_host: str = "",
) -> None:
    registrar_log_email(
        operador,
        STATUS_ACEITO_SMTP,
        tipo,
        destinatario,
        remetente=remetente,
        assunto=assunto,
        recibo_id=recibo_id,
        recibo_numero=recibo_numero,
        contribuinte_id=contribuinte_id,
        contribuinte_nome=contribuinte_nome,
        entrega=ENTREGA_ACEITO_SERVIDOR,
        leitura=LEITURA_NAO_RASTREADO,
        smtp_host=smtp_host,
    )


def log_email_falha(
    operador: str,
    tipo: str,
    destinatario: str,
    erro: str,
    *,
    remetente: str = "",
    assunto: str = "",
    recibo_id: int | None = None,
    recibo_numero: str = "",
    contribuinte_id: int | None = None,
    contribuinte_nome: str = "",
    smtp_host: str = "",
) -> None:
    registrar_log_email(
        operador,
        STATUS_FALHA,
        tipo,
        destinatario,
        remetente=remetente,
        assunto=assunto,
        recibo_id=recibo_id,
        recibo_numero=recibo_numero,
        contribuinte_id=contribuinte_id,
        contribuinte_nome=contribuinte_nome,
        entrega=ENTREGA_NAO_RASTREADO,
        leitura=LEITURA_NAO_RASTREADO,
        smtp_host=smtp_host,
        erro=erro,
    )


def log_teste_smtp(operador: str, sucesso: bool, mensagem: str, smtp_host: str) -> None:
    registrar_log_email(
        operador,
        STATUS_TESTE_SMTP,
        "TESTE_CONFIG",
        destinatario="(teste)",
        smtp_host=smtp_host,
        erro="" if sucesso else mensagem,
        entrega=ENTREGA_ACEITO_SERVIDOR if sucesso else ENTREGA_NAO_RASTREADO,
        leitura=LEITURA_NAO_RASTREADO,
        assunto=mensagem if sucesso else "",
    )
