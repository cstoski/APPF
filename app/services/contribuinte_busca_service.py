"""Campos e helpers de busca rápida (sem descriptografar todos os contribuintes)."""
from __future__ import annotations

import hashlib
import unicodedata


def hash_cpf_busca(cpf_norm: str) -> str | None:
    if not cpf_norm or len(cpf_norm) != 11:
        return None
    return hashlib.sha256(cpf_norm.encode("utf-8")).hexdigest()


def normalizar_nome_busca(nome: str) -> str:
    s = (nome or "").strip().lower()
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch))
