from __future__ import annotations

import hashlib
import hmac
import re
from datetime import date, timedelta
from typing import Optional

from fastapi import HTTPException, status

from app.config.license_signing import obter_chave_assinatura_licenca

VALIDADE_DIAS = 365
VALIDADE_DIAS_DEMO = 3
SERIAL_VERSAO = "v1"

# Serial fixo global — modo demonstração (3 dias, uma vez por equipamento)
SERIAL_DEMO_CANONICO = "DEMO-APPF-DEMO-3DAY"

# Seriais antigos (revogados) — não aceitar ativação nem vigência
_COMPACT_REVOGADOS = frozenset({"PROAPPF2026", "APPF2026SGCVLOCL"})


def eh_serial_demo(bruto: str) -> bool:
    compact = re.sub(r"[^A-Za-z0-9]", "", (bruto or "")).upper()
    demo_compact = re.sub(r"[^A-Za-z0-9]", "", SERIAL_DEMO_CANONICO).upper()
    return compact == demo_compact


def serial_revogado(bruto: str) -> bool:
    compact = re.sub(r"[^A-Za-z0-9]", "", (bruto or "")).upper()
    return compact in _COMPACT_REVOGADOS


def _somente_alfanum16(bruto: str) -> Optional[str]:
    alnum = re.sub(r"[^A-Za-z0-9]", "", (bruto or "")).upper()
    if len(alnum) != 16:
        return None
    return f"{alnum[0:4]}-{alnum[4:8]}-{alnum[8:12]}-{alnum[12:16]}"


def normalizar_serial_entrada(bruto: str) -> str:
    if eh_serial_demo(bruto):
        return SERIAL_DEMO_CANONICO
    if serial_revogado(bruto):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este serial foi descontinuado. Solicite um novo código ao suporte informando o HWID.",
        )
    out = _somente_alfanum16(bruto)
    if not out:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Serial inválido: são necessários 16 caracteres alfanuméricos "
            "(grupos XXXX-XXXX-XXXX-XXXX; hífens opcionais).",
        )
    return out


def gerar_serial_para_hwid(hwid: str, data_emissao: Optional[date] = None) -> str:
    """Gera serial vinculado ao HWID e à data de emissão (uso do fornecedor)."""
    emissao = data_emissao or date.today()
    msg = f"{SERIAL_VERSAO}|{hwid.strip()}|{VALIDADE_DIAS}|{emissao.isoformat()}".encode("utf-8")
    digest = hmac.new(obter_chave_assinatura_licenca(), msg, hashlib.sha256).hexdigest()[:16].upper()
    return f"{digest[0:4]}-{digest[4:8]}-{digest[8:12]}-{digest[12:16]}"


def resolver_emissao_serial(hwid: str, serial: str) -> date:
    """Retorna a data de emissão embutida no serial assinado para este HWID."""
    canon = normalizar_serial_entrada(serial)

    limite_busca = VALIDADE_DIAS + 60
    hoje = date.today()
    for dias_atras in range(0, limite_busca):
        candidata = hoje - timedelta(days=dias_atras)
        if gerar_serial_para_hwid(hwid, candidata) == canon:
            return candidata

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Serial não reconhecido para este equipamento (HWID). "
        "Solicite um novo código ao suporte informando o HWID exibido na tela.",
    )
