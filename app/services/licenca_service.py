from __future__ import annotations

import hashlib
import hmac
import subprocess
from datetime import datetime
from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.sys_models import LicencaAtivada

SERIAL_VALIDO = "PRO-APPF-2026"
HMAC_SALT = b"APPF_LOCAL_LICENSE_SALT_V1"


def obter_hwid_windows() -> str:
    """
    Extrai HWID via WMIC (Windows) com fallback por PowerShell.
    Totalmente offline.
    """
    # WMIC csproduct get uuid
    try:
        out = subprocess.check_output(
            ["wmic", "csproduct", "get", "uuid"],
            stderr=subprocess.STDOUT,
            text=True,
            shell=False,
        ).strip()
        lines = [l.strip() for l in out.splitlines() if l.strip()]
        # Esperado: ["UUID", "<valor>"]
        if len(lines) >= 2 and lines[1]:
            return lines[1]
    except Exception:
        pass

    # Fallback PowerShell
    try:
        out = subprocess.check_output(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "(Get-CimInstance Win32_ComputerSystemProduct).UUID",
            ],
            stderr=subprocess.STDOUT,
            text=True,
            shell=False,
        ).strip()
        if out:
            return out
    except Exception:
        pass

    # Último recurso: hash de hostname + CPU id (quando wmic/cim falham)
    import os

    seed = (
        os.environ.get("COMPUTERNAME", "")
        + os.environ.get("PROCESSOR_IDENTIFIER", "")
        + os.environ.get("USERNAME", "")
    ).encode("utf-8")
    return hashlib.sha256(seed).hexdigest()


def _assinatura_licenca(hwid: str, serial: str) -> str:
    """
    Assinatura HMAC offline a partir do HWID e serial.
    """
    msg = f"{hwid}|{serial}".encode("utf-8")
    sig = hmac.new(HMAC_SALT, msg, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(sig).decode("utf-8")


def validar_serial(serial: str) -> None:
    if serial.strip() != SERIAL_VALIDO:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Serial inválido para ativação offline.",
        )


def ativar_licenca(db: Session, serial: str) -> str:
    validar_serial(serial)
    hwid = obter_hwid_windows()
    assinatura = _assinatura_licenca(hwid, serial)

    existente = db.query(LicencaAtivada).filter(LicencaAtivada.hwid == hwid).first()
    if existente:
        existente.serial = serial
        existente.assinatura = assinatura
        existente.ativa = True
        existente.data_ativacao = datetime.utcnow()
        db.commit()
        return hwid

    nova = LicencaAtivada(
        hwid=hwid,
        serial=serial,
        assinatura=assinatura,
        ativa=True,
        data_ativacao=datetime.utcnow(),
    )
    db.add(nova)
    db.commit()
    return hwid


def status_licenca(db: Session) -> Optional[LicencaAtivada]:
    hwid = obter_hwid_windows()
    lic = db.query(LicencaAtivada).filter(LicencaAtivada.hwid == hwid).first()
    return lic


def verificar_licenca_ativa(db: Session) -> None:
    hwid = obter_hwid_windows()
    lic = (
        db.query(LicencaAtivada)
        .filter(LicencaAtivada.hwid == hwid, LicencaAtivada.ativa == True)  # noqa: E712
        .first()
    )
    if not lic:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sistema não ativado. Ative a licença nesta máquina para operar.",
        )

    esperado = _assinatura_licenca(hwid, lic.serial)
    if not hmac.compare_digest(esperado, lic.assinatura):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Licença inválida ou adulterada nesta máquina.",
        )

    if lic.serial.strip() != SERIAL_VALIDO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Serial não autorizado para esta versão.",
        )


def require_licenca(db: Session = Depends(get_db)) -> None:
    """
    Dependência para bloquear rotas operacionais.
    """
    verificar_licenca_ativa(db)

import base64
