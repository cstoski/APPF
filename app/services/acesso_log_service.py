from __future__ import annotations

from datetime import datetime
from app.runtime_paths import get_logs_dir

LOG_DIR = get_logs_dir()
LOG_FILE = LOG_DIR / "acesso.log"


def registrar_log_acesso(
    operador: str,
    acao: str,
    alvo: str = "",
    detalhes: str = "",
) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha = f"{ts} | operador={operador.strip()} | acao={acao}"
    if alvo:
        linha += f" | alvo={alvo.strip()}"
    if detalhes:
        linha += f" | {detalhes}"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def log_login(username: str, perfil: str) -> None:
    registrar_log_acesso(username, "LOGIN", alvo=username, detalhes=f"perfil={perfil}")


def log_login_falha(username: str) -> None:
    registrar_log_acesso(username or "(vazio)", "LOGIN_FALHA", alvo=username or "(vazio)")


def log_logout(username: str) -> None:
    registrar_log_acesso(username, "LOGOUT", alvo=username)


def log_usuario_criar(operador: str, username: str, perfil: str) -> None:
    registrar_log_acesso(
        operador,
        "USUARIO_CRIAR",
        alvo=username,
        detalhes=f"perfil={perfil}",
    )


def log_usuario_alterar(operador: str, alvo: str, detalhes: str) -> None:
    registrar_log_acesso(operador, "USUARIO_ALTERAR", alvo=alvo, detalhes=detalhes)


def log_usuario_desativar(operador: str, alvo: str) -> None:
    registrar_log_acesso(operador, "USUARIO_DESATIVAR", alvo=alvo)


def log_senha_alterada_propria(username: str) -> None:
    registrar_log_acesso(username, "SENHA_ALTERAR", alvo=username, detalhes="alteracao=propria")


def log_senha_alterada_admin(operador: str, alvo: str) -> None:
    registrar_log_acesso(operador, "SENHA_ALTERAR", alvo=alvo, detalhes="alteracao=administrador")
