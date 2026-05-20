from __future__ import annotations

import base64
import hashlib
import hmac
import subprocess
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Literal, Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.sys_models import LicencaAtivada, LicencaEvento
from app.schemas.sys_schemas import LicencaStatusOut
from app.services.licenca_log_service import mascarar_serial, registrar_log_licenca
from app.services.licenca_serial_service import (
    SERIAL_DEMO_CANONICO,
    VALIDADE_DIAS,
    VALIDADE_DIAS_DEMO,
    eh_serial_demo,
    normalizar_serial_entrada,
    resolver_emissao_serial,
    serial_revogado,
)

GRACE_DIAS = 7
AVISO_EXPIRACAO_DIAS = 30
HMAC_SALT = b"APPF_LOCAL_LICENSE_SALT_V1"

ModoLicenca = Literal["ATIVA", "GRACE", "EXPIRADA", "DEMO_EXPIRADA", "NAO_ATIVADA", "INTEGRIDADE_FALHA"]


@dataclass
class EstadoLicenca:
    modo: ModoLicenca
    ativa: bool
    registrada: bool
    expirada: bool
    integridade_ok: bool
    hwid: str
    serial: str
    data_ativacao: Optional[datetime]
    data_expiracao: Optional[datetime]
    data_emissao_serial: Optional[date]
    dias_restantes: Optional[int]
    grace_dias_restantes: Optional[int]
    pode_leitura: bool
    pode_escrita: bool
    aviso_expiracao: bool
    tipo_licenca: str = "PRODUCAO"
    demo_consumido: bool = False


def obter_hwid_windows() -> str:
    try:
        out = subprocess.check_output(
            ["wmic", "csproduct", "get", "uuid"],
            stderr=subprocess.STDOUT,
            text=True,
            shell=False,
        ).strip()
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        if len(lines) >= 2 and lines[1]:
            return lines[1]
    except Exception:
        pass

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

    import os

    seed = (
        os.environ.get("COMPUTERNAME", "")
        + os.environ.get("PROCESSOR_IDENTIFIER", "")
        + os.environ.get("USERNAME", "")
    ).encode("utf-8")
    return hashlib.sha256(seed).hexdigest()


def calcular_data_expiracao(data_emissao: date) -> datetime:
    base = datetime.combine(data_emissao, datetime.min.time())
    return base + timedelta(days=VALIDADE_DIAS)


def _assinatura_registro(hwid: str, serial: str) -> str:
    msg = f"{hwid}|{serial}".encode("utf-8")
    sig = hmac.new(HMAC_SALT, msg, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(sig).decode("utf-8")


def _registrar_evento_db(
    db: Session,
    hwid: str,
    operador: str,
    acao: str,
    serial: str = "",
    detalhes: str = "",
) -> None:
    ev = LicencaEvento(
        hwid=hwid,
        operador_username=operador,
        acao=acao,
        serial_mascarado=mascarar_serial(serial) if serial else "",
        detalhes=detalhes or None,
    )
    db.add(ev)


def ativar_licenca(db: Session, serial: str, operador: str = "sistema") -> str:
    serial_armazenar = normalizar_serial_entrada(serial)
    hwid = obter_hwid_windows()
    existente = db.query(LicencaAtivada).filter(LicencaAtivada.hwid == hwid).first()
    agora = datetime.utcnow()

    if eh_serial_demo(serial_armazenar):
        if existente and existente.demo_consumido:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "O serial de demonstração já foi utilizado neste equipamento e não pode ser "
                    "reativado. Solicite uma licença comercial (serial gerado para o HWID)."
                ),
            )
        if existente and existente.tipo_licenca == "PRODUCAO" and agora <= _data_fim_vigencia(existente):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe licença comercial em vigor. O modo demonstração não se aplica.",
            )

        expira = agora + timedelta(days=VALIDADE_DIAS_DEMO)
        assinatura = _assinatura_registro(hwid, serial_armazenar)
        acao = "ATIVAR_DEMO"
        if existente:
            existente.serial = serial_armazenar
            existente.assinatura = assinatura
            existente.tipo_licenca = "DEMO"
            existente.demo_consumido = True
            existente.ativa = True
            existente.data_ativacao = agora
            existente.data_expiracao = expira
            existente.data_emissao_serial = agora
        else:
            db.add(
                LicencaAtivada(
                    hwid=hwid,
                    serial=serial_armazenar,
                    assinatura=assinatura,
                    tipo_licenca="DEMO",
                    demo_consumido=True,
                    ativa=True,
                    data_ativacao=agora,
                    data_expiracao=expira,
                    data_emissao_serial=agora,
                )
            )
        _registrar_evento_db(
            db,
            hwid,
            operador,
            acao,
            serial=serial_armazenar,
            detalhes=f"validade_dias={VALIDADE_DIAS_DEMO} expira={expira.isoformat()}",
        )
        db.commit()
        registrar_log_licenca(
            operador,
            acao,
            hwid,
            serial_mascarado=mascarar_serial(serial_armazenar),
            detalhes=f"demo expira={expira.date().isoformat()}",
        )
        return hwid

    data_emissao = resolver_emissao_serial(hwid, serial_armazenar)
    assinatura = _assinatura_registro(hwid, serial_armazenar)
    expira = calcular_data_expiracao(data_emissao)
    acao = "RENOVAR" if existente else "ATIVAR"
    if existente:
        existente.serial = serial_armazenar
        existente.assinatura = assinatura
        existente.tipo_licenca = "PRODUCAO"
        existente.ativa = True
        existente.data_ativacao = agora
        existente.data_expiracao = expira
        existente.data_emissao_serial = datetime.combine(data_emissao, datetime.min.time())
    else:
        db.add(
            LicencaAtivada(
                hwid=hwid,
                serial=serial_armazenar,
                assinatura=assinatura,
                tipo_licenca="PRODUCAO",
                demo_consumido=False,
                ativa=True,
                data_ativacao=agora,
                data_expiracao=expira,
                data_emissao_serial=datetime.combine(data_emissao, datetime.min.time()),
            )
        )

    _registrar_evento_db(
        db,
        hwid,
        operador,
        acao,
        serial=serial_armazenar,
        detalhes=f"validade_dias={VALIDADE_DIAS} expira={expira.isoformat()}",
    )
    db.commit()

    registrar_log_licenca(
        operador,
        acao,
        hwid,
        serial_mascarado=mascarar_serial(serial_armazenar),
        detalhes=f"expira={expira.date().isoformat()}",
    )
    return hwid


def status_licenca(db: Session) -> Optional[LicencaAtivada]:
    hwid = obter_hwid_windows()
    return db.query(LicencaAtivada).filter(LicencaAtivada.hwid == hwid).first()


def _data_fim_vigencia(lic: LicencaAtivada) -> datetime:
    if lic.data_expiracao is not None:
        return lic.data_expiracao
    base = lic.data_emissao_serial or lic.data_ativacao
    if isinstance(base, datetime):
        return base + timedelta(days=VALIDADE_DIAS)
    return lic.data_ativacao + timedelta(days=VALIDADE_DIAS)


def _avaliar_estado(lic: Optional[LicencaAtivada], hwid: str) -> EstadoLicenca:
    if not lic:
        return EstadoLicenca(
            modo="NAO_ATIVADA",
            ativa=False,
            registrada=False,
            expirada=False,
            integridade_ok=False,
            hwid=hwid,
            serial="",
            data_ativacao=None,
            data_expiracao=None,
            data_emissao_serial=None,
            dias_restantes=None,
            grace_dias_restantes=None,
            pode_leitura=False,
            pode_escrita=False,
            aviso_expiracao=False,
            tipo_licenca="PRODUCAO",
            demo_consumido=False,
        )

    agora = datetime.utcnow()
    tipo = (lic.tipo_licenca or "PRODUCAO").strip().upper()
    demo_flag = bool(lic.demo_consumido)

    if serial_revogado(lic.serial):
        return EstadoLicenca(
            modo="NAO_ATIVADA",
            ativa=False,
            registrada=True,
            expirada=True,
            integridade_ok=False,
            hwid=lic.hwid,
            serial=lic.serial,
            data_ativacao=lic.data_ativacao,
            data_expiracao=_data_fim_vigencia(lic),
            data_emissao_serial=None,
            dias_restantes=None,
            grace_dias_restantes=None,
            pode_leitura=False,
            pode_escrita=False,
            aviso_expiracao=False,
            tipo_licenca=tipo,
            demo_consumido=demo_flag,
        )

    esperado = _assinatura_registro(hwid, lic.serial)
    integridade_ok = hmac.compare_digest(esperado, lic.assinatura)
    fim = _data_fim_vigencia(lic)
    expirada = agora > fim

    dias_restantes: Optional[int] = None
    grace_dias_restantes: Optional[int] = None
    if not expirada:
        dias_restantes = max(0, (fim - agora).days)
    elif tipo != "DEMO":
        fim_grace = fim + timedelta(days=GRACE_DIAS)
        if agora <= fim_grace:
            grace_dias_restantes = max(0, (fim_grace - agora).days)

    aviso_expiracao = (
        not expirada
        and dias_restantes is not None
        and dias_restantes <= AVISO_EXPIRACAO_DIAS
        and tipo != "DEMO"
    )

    if not integridade_ok:
        modo: ModoLicenca = "INTEGRIDADE_FALHA"
    elif not expirada and lic.ativa:
        modo = "ATIVA"
    elif expirada and tipo == "DEMO":
        modo = "DEMO_EXPIRADA"
    elif expirada and grace_dias_restantes is not None:
        modo = "GRACE"
    elif expirada:
        modo = "EXPIRADA"
    else:
        modo = "NAO_ATIVADA"

    pode_escrita = modo == "ATIVA" and integridade_ok
    pode_leitura = modo in ("ATIVA", "GRACE") and integridade_ok
    ativa = modo == "ATIVA"

    emissao: Optional[date] = None
    if lic.data_emissao_serial:
        emissao = lic.data_emissao_serial.date() if isinstance(lic.data_emissao_serial, datetime) else lic.data_emissao_serial

    return EstadoLicenca(
        modo=modo,
        ativa=ativa,
        registrada=True,
        expirada=expirada,
        integridade_ok=integridade_ok,
        hwid=lic.hwid,
        serial=lic.serial,
        data_ativacao=lic.data_ativacao,
        data_expiracao=fim,
        data_emissao_serial=emissao,
        dias_restantes=dias_restantes,
        grace_dias_restantes=grace_dias_restantes,
        pode_leitura=pode_leitura,
        pode_escrita=pode_escrita,
        aviso_expiracao=aviso_expiracao,
        tipo_licenca=tipo,
        demo_consumido=demo_flag,
    )


def montar_status_licenca(db: Session) -> LicencaStatusOut:
    hwid = obter_hwid_windows()
    estado = _avaliar_estado(status_licenca(db), hwid)
    return LicencaStatusOut(
        ativa=estado.ativa,
        registrada=estado.registrada,
        expirada=estado.expirada,
        integridade_ok=estado.integridade_ok,
        hwid=estado.hwid,
        serial=estado.serial,
        data_ativacao=estado.data_ativacao,
        data_expiracao=estado.data_expiracao,
        data_emissao_serial=estado.data_emissao_serial,
        dias_restantes=estado.dias_restantes,
        grace_dias_restantes=estado.grace_dias_restantes,
        validade_dias=VALIDADE_DIAS_DEMO if estado.tipo_licenca == "DEMO" else VALIDADE_DIAS,
        grace_dias=GRACE_DIAS,
        modo=estado.modo,
        pode_leitura=estado.pode_leitura,
        pode_escrita=estado.pode_escrita,
        aviso_expiracao=estado.aviso_expiracao,
        tipo_licenca=estado.tipo_licenca,
        eh_demo=estado.tipo_licenca == "DEMO",
        demo_consumido=estado.demo_consumido,
        serial_demo=SERIAL_DEMO_CANONICO,
    )


def _erro_licenca(estado: EstadoLicenca, escrita: bool) -> HTTPException:
    if estado.modo == "NAO_ATIVADA":
        detail = "Sistema não ativado. O perfil MASTER deve ativar a licença neste computador."
    elif estado.modo == "INTEGRIDADE_FALHA":
        detail = "Licença inválida ou adulterada nesta máquina. Contate o suporte técnico."
    elif estado.modo == "GRACE" and escrita:
        detail = (
            f"Licença expirada há mais de 0 dias. Período de cortesia: {estado.grace_dias_restantes or 0} "
            f"dia(s) restante(s) apenas para consulta. Renove a licença para emitir recibos."
        )
    elif estado.modo == "DEMO_EXPIRADA":
        detail = (
            "Período de demonstração encerrado (3 dias). O serial demo não pode ser reutilizado. "
            "Solicite licença comercial com o HWID deste equipamento."
        )
    elif estado.modo == "EXPIRADA":
        detail = "Licença expirada. O perfil MASTER deve renovar a ativação em Configuração → Licença."
    else:
        detail = "Licença não permite esta operação."

    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def verificar_licenca_leitura(db: Session) -> EstadoLicenca:
    estado = _avaliar_estado(status_licenca(db), obter_hwid_windows())
    if not estado.pode_leitura:
        raise _erro_licenca(estado, escrita=False)
    return estado


def verificar_licenca_escrita(db: Session) -> EstadoLicenca:
    estado = _avaliar_estado(status_licenca(db), obter_hwid_windows())
    if not estado.pode_escrita:
        raise _erro_licenca(estado, escrita=True)
    return estado


def licenca_operacional(db: Session) -> bool:
    estado = _avaliar_estado(status_licenca(db), obter_hwid_windows())
    return estado.pode_escrita


def require_licenca(db: Session = Depends(get_db)) -> None:
    verificar_licenca_leitura(db)


def require_licenca_escrita(db: Session = Depends(get_db)) -> None:
    verificar_licenca_escrita(db)


def registrar_falha_ativacao(db: Session, operador: str, serial: str, motivo: str) -> None:
    hwid = obter_hwid_windows()
    try:
        _registrar_evento_db(db, hwid, operador, "FALHA_ATIVAR", serial=serial, detalhes=motivo)
        db.commit()
    except Exception:
        db.rollback()
    registrar_log_licenca(operador, "FALHA_ATIVAR", hwid, serial_mascarado=mascarar_serial(serial), detalhes=motivo)
