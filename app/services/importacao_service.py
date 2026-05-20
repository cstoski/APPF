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
}


def normalizar_nome(nome: str) -> str:
    return " ".join(str(nome).strip().split()).casefold()


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

    keep = [c for c in df.columns if c in COLUNAS_ACEITAS.keys()]
    return df[keep].copy() if keep else df.iloc[:, 0:0].copy()


def ler_planilha(file_bytes: bytes, filename: str) -> pd.DataFrame:
    name = filename.lower().strip()
    bio = BytesIO(file_bytes)

    if name.endswith(".csv"):
        df = pd.read_csv(bio, dtype=str)
    else:
        df = pd.read_excel(bio, dtype=str, engine="openpyxl")

    df = _mapear_colunas(df)
    df = df.fillna("")

    if "cpf" in df.columns:
        df["cpf"] = df["cpf"].astype(str).apply(normalizar_cpf)

    return df


def _linha_duplicada_existente(
    nome: str,
    cpf: str,
    cpfs_set: set,
    nomes_set: set,
) -> bool:
    nome_norm = normalizar_nome(nome)
    if cpf and cpf in cpfs_set:
        return True
    if nome_norm and nome_norm in nomes_set:
        return True
    return False


def gerar_preview(df: pd.DataFrame, cpfs_existentes: List[str], nomes_existentes: List[str]) -> PreviewImportacao:
    total = len(df)
    duplicados: List[str] = []
    novos = 0

    cpfs_set = set(c for c in cpfs_existentes if c)
    nomes_set = set(n for n in nomes_existentes if n)

    for _, row in df.iterrows():
        nome = str(row.get("nome_completo", "")).strip()
        cpf = normalizar_cpf(str(row.get("cpf", "")))

        if _linha_duplicada_existente(nome, cpf, cpfs_set, nomes_set):
            duplicados.append(f"{nome} | {cpf or '(sem CPF)'}")
        else:
            novos += 1

    return PreviewImportacao(
        total_linhas=total,
        novos=novos,
        duplicados=len(duplicados),
        exemplos_duplicados=duplicados[:10],
    )


def gerar_preview_detalhado(df, cpfs_existentes, nomes_existentes):
    itens = []
    novos = duplicados = invalidos = 0
    exemplos_duplicados = []

    cpfs_set = set(c for c in cpfs_existentes if c)
    nomes_set = set(n for n in nomes_existentes if n)

    cpfs_lote: set[str] = set()
    nomes_lote: set[str] = set()

    for offset, (_, row) in enumerate(df.iterrows()):
        linha = offset + 2

        nome = str(row.get("nome_completo", "")).strip()
        cpf = normalizar_cpf(str(row.get("cpf", "")))
        email = str(row.get("email", "")).strip()
        telefone = str(row.get("telefone", "")).strip()

        erros = []

        if not validar_nome(nome):
            erros.append("Nome obrigatório (mín. 3 caracteres)")

        if not validar_cpf_opcional(cpf):
            erros.append("CPF inválido (use 11 dígitos ou deixe vazio)")

        if not validar_email(email):
            erros.append("E-mail inválido")

        if not validar_telefone(telefone):
            erros.append("Telefone inválido")

        if erros:
            status = "INVALIDO"
            sugestao = "PULAR"
            invalidos += 1
        elif cpf and cpf in cpfs_lote:
            status = "DUP_ARQUIVO"
            sugestao = "PULAR"
            duplicados += 1
        elif normalizar_nome(nome) in nomes_lote:
            status = "DUP_ARQUIVO"
            sugestao = "PULAR"
            duplicados += 1
        elif _linha_duplicada_existente(nome, cpf, cpfs_set, nomes_set):
            if cpf and cpf in cpfs_set:
                status = "DUP_CPF"
            else:
                status = "DUP_NOME"
            sugestao = "PULAR"
            duplicados += 1
        else:
            status = "NOVO"
            sugestao = "IMPORTAR"
            novos += 1

        if cpf:
            cpfs_lote.add(cpf)
        nome_norm = normalizar_nome(nome)
        if nome_norm:
            nomes_lote.add(nome_norm)

        itens.append({
            "linha": linha,
            "nome_completo": nome,
            "cpf": cpf,
            "email": email,
            "telefone": telefone,
            "status": status,
            "sugestao_acao": sugestao,
            "erros": erros,
        })

        if "DUP" in status and len(exemplos_duplicados) < 10:
            exemplos_duplicados.append(f"{nome} | {cpf or '(sem CPF)'}")

    return {
        "total_linhas": len(df),
        "novos": novos,
        "duplicados": duplicados,
        "invalidos": invalidos,
        "sem_consentimento": 0,
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


def validar_cpf_opcional(cpf: str) -> bool:
    if not cpf:
        return True
    return len(cpf) == 11


# compatibilidade
def validar_cpf_simples(cpf: str) -> bool:
    return validar_cpf_opcional(cpf)
