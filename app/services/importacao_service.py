from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Tuple, List, Dict, Optional

import pandas as pd

from app.services.seguranca_service import normalizar_cpf


@dataclass
class PreviewImportacao:
    total_linhas: int
    novos: int
    duplicados: int
    exemplos_duplicados: List[str]


COLUNAS_ACEITAS = {
    "nome_completo": ["nome", "nome_completo", "contribuinte", "nome do contribuinte"],
    "cpf": ["cpf", "documento", "cpf do contribuinte"],
    "email": ["email", "e-mail"],
    "telefone": ["telefone", "celular", "fone"],
    "consentimento_lgpd": ["consentimento_lgpd", "consentimento", "lgpd"],
    "observacoes": ["observacoes", "obs", "observação"],
}


def _mapear_colunas(df: pd.DataFrame) -> pd.DataFrame:
    cols_lower = {c: str(c).strip().lower() for c in df.columns}
    inv = {v: k for k, v in cols_lower.items()}

    def find_col(keys: List[str]) -> Optional[str]:
        for k in keys:
            if k in inv:
                return inv[k]
        return None

    mapping = {}
    for canonical, aliases in COLUNAS_ACEITAS.items():
        col = find_col(aliases)
        if col:
            mapping[col] = canonical

    df = df.rename(columns=mapping)

    # Mantém apenas colunas conhecidas
    keep = [c for c in df.columns if c in COLUNAS_ACEITAS.keys()]
    df = df[keep].copy()

    return df


def ler_planilha(file_bytes: bytes, filename: str) -> pd.DataFrame:
    name = filename.lower().strip()
    bio = BytesIO(file_bytes)

    if name.endswith(".csv"):
        df = pd.read_csv(bio, dtype=str)
    else:
        df = pd.read_excel(bio, dtype=str, engine="openpyxl")

    df = _mapear_colunas(df)
    df = df.fillna("")

    # Normalizações
    if "cpf" in df.columns:
        df["cpf"] = df["cpf"].astype(str).apply(normalizar_cpf)

    if "consentimento_lgpd" in df.columns:
        def to_bool(v: str) -> bool:
            s = str(v).strip().lower()
            return s in {"1", "true", "sim", "s", "yes", "y", "ok"}
        df["consentimento_lgpd"] = df["consentimento_lgpd"].apply(to_bool)

    return df


def gerar_preview(df: pd.DataFrame, cpfs_existentes: List[str], nomes_existentes: List[str]) -> PreviewImportacao:
    """
    Duplicidade por CPF (prioritário) ou Nome (fallback).
    cpfs_existentes aqui são CPFs em texto (já decifrados e normalizados).
    """
    total = len(df)

    duplicados = []
    novos = 0

    for _, row in df.iterrows():
        nome = str(row.get("nome_completo", "")).strip().lower()
        cpf = normalizar_cpf(str(row.get("cpf", "")))
        is_dup = False

        if cpf and cpf in cpfs_existentes:
            is_dup = True
        elif nome and nome in nomes_existentes:
            is_dup = True

        if is_dup:
            duplicados.append(f"{nome} | {cpf}")
        else:
            novos += 1

    exemplos = duplicados[:10]
    return PreviewImportacao(
        total_linhas=total,
        novos=novos,
        duplicados=len(duplicados),
        exemplos_duplicados=exemplos,
    )