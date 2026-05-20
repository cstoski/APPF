"""Rastreamento em memória de usuários com atividade recente (sessões ativas)."""
from __future__ import annotations

import threading
import time
from typing import List

_lock = threading.Lock()
_atividade: dict[str, float] = {}
TIMEOUT_SEGUNDOS = 300  # 5 min sem requisição autenticada = desconectado


def registrar_atividade(username: str) -> None:
    if not (username or "").strip():
        return
    with _lock:
        _atividade[username.strip()] = time.time()


def remover_atividade(username: str) -> None:
    if not (username or "").strip():
        return
    with _lock:
        _atividade.pop(username.strip(), None)


def listar_usuarios_conectados(timeout_segundos: int = TIMEOUT_SEGUNDOS) -> List[str]:
    agora = time.time()
    limite = max(60, int(timeout_segundos))
    with _lock:
        ativos = [u for u, ts in _atividade.items() if agora - ts < limite]
    return sorted(ativos)


def contar_usuarios_conectados(timeout_segundos: int = TIMEOUT_SEGUNDOS) -> int:
    return len(listar_usuarios_conectados(timeout_segundos))
