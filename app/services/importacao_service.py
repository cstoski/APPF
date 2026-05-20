from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Tuple, List, Dict, Optional

import pandas as pd
import re

from app.services.seguranca_service import normalizar_cpf, mascarar_cpf


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
    

def gerar_preview_detalhado(df, cpfs_existentes, nomes_existentes):
    itens = []
    novos = duplicados = invalidos = sem_consent = 0
    exemplos_duplicados = []

    cpfs_set = set([c for c in cpfs_existentes if c])
    nomes_set = set([n for n in nomes_existentes if n])

    cpfs_lote = set()  # ✅ detectar duplicado dentro do próprio arquivo

    for idx, row in df.iterrows():
        linha = int(idx) + 2

        nome = str(row.get("nome_completo", "")).strip()
        cpf = normalizar_cpf(str(row.get("cpf", "")))
        email = str(row.get("email", "")).strip()
        telefone = str(row.get("telefone", "")).strip()
        consent = bool(row.get("consentimento_lgpd", False))

        # =========================
        # VALIDAÇÕES
        # =========================
        erros = []

        if not validar_nome(nome):
            erros.append("Nome inválido")

        if not validar_cpf_simples(cpf):
            erros.append("CPF inválido")

        if not validar_email(email):
            erros.append("Email inválido")

        if not validar_telefone(telefone):
            erros.append("Telefone inválido")

        if not consent:
            status = "SEM_CONSENTIMENTO"
            sugestao = "PULAR"
            sem_consent += 1

        elif erros:
            status = "INVALIDO"
            sugestao = "PULAR"
            invalidos += 1

        elif cpf in cpfs_lote:
            status = "DUP_ARQUIVO"
            sugestao = "PULAR"
            duplicados += 1

        elif cpf in cpfs_set:
            status = "DUP_CPF"
            sugestao = "PULAR"
            duplicados += 1

        elif nome.lower() in nomes_set:
            status = "DUP_NOME"
            sugestao = "PULAR"
            duplicados += 1

        else:
            status = "NOVO"
            sugestao = "IMPORTAR"
            novos += 1

        cpfs_lote.add(cpf)

        itens.append({
            "linha": linha,
            "nome_completo": nome,
            "cpf": cpf,
            "status": status,
            "sugestao_acao": sugestao,
            "erros": erros,  # ✅ novo
        })

        if "DUP" in status and len(exemplos_duplicados) < 10:
            exemplos_duplicados.append(f"{nome} | {cpf}")

    return {
        "total_linhas": len(df),
        "novos": novos,
        "duplicados": duplicados,
        "invalidos": invalidos,
        "sem_consentimento": sem_consent,
        "exemplos_duplicados": exemplos_duplicados,
        "itens": itens,
    }


def validar_email(email: str) -> bool:
    if not email:
        return True
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

def validar_telefone(tel: str) -> bool:
    if not tel:
        return True
    return len(re.sub(r"\D", "", tel)) >= 8

def validar_nome(nome: str) -> bool:
    return len(nome.strip()) >= 3


def validar_cpf_simples(cpf: str) -> bool:
    return len(cpf) >= 11
