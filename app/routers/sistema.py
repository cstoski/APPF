from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.schemas.sys_schemas import LicencaAtivarIn, LicencaAtivarOut, LicencaStatusOut
from app.services.licenca_service import ativar_licenca, status_licenca, obter_hwid_windows

router = APIRouter(prefix="/api/v1", tags=["Sistema"])


@router.get("/licenca", response_model=LicencaStatusOut)
def get_licenca(db: Session = Depends(get_db)) -> LicencaStatusOut:
    lic = status_licenca(db)
    if not lic:
        # Retorna status "não ativada" com hwid atual
        from datetime import datetime
        return LicencaStatusOut(
            ativa=False,
            hwid=obter_hwid_windows(),
            serial="",
            data_ativacao=datetime.utcfromtimestamp(0),
        )
    return LicencaStatusOut(
        ativa=bool(lic.ativa),
        hwid=lic.hwid,
        serial=lic.serial,
        data_ativacao=lic.data_ativacao,
    )


@router.post("/licenca/ativar", response_model=LicencaAtivarOut)
def post_ativar_licenca(body: LicencaAtivarIn, db: Session = Depends(get_db)) -> LicencaAtivarOut:
    hwid = ativar_licenca(db, body.serial)
    return LicencaAtivarOut(ativa=True, mensagem=f"Licença ativada nesta máquina (HWID: {hwid}).")