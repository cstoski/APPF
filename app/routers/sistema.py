from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.schemas.sys_schemas import LicencaAtivarIn, LicencaAtivarOut, LicencaStatusOut
from app.services.licenca_service import (
    ativar_licenca,
    montar_status_licenca,
    registrar_falha_ativacao,
)
from app.services.seguranca_service import get_current_username, require_roles

router = APIRouter(prefix="/api/v1", tags=["Sistema"])


@router.get("/sistema/info")
def get_sistema_info():
    return {
        "nome": "Contribuições APPF",
        "produto": "SGCV",
        "versao": "1.0.0",
        "build": "offline-local",
    }


@router.get("/licenca", response_model=LicencaStatusOut)
def get_licenca(db: Session = Depends(get_db)) -> LicencaStatusOut:
    return montar_status_licenca(db)


@router.post(
    "/licenca/ativar",
    response_model=LicencaAtivarOut,
    dependencies=[Depends(require_roles("MASTER"))],
)
def post_ativar_licenca(
    body: LicencaAtivarIn,
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
) -> LicencaAtivarOut:
    try:
        ativar_licenca(db, body.serial, operador=operador)
    except HTTPException as exc:
        registrar_falha_ativacao(db, operador, body.serial, str(exc.detail))
        raise
    st = montar_status_licenca(db)
    if st.ativa:
        msg = "Licença ativada com sucesso. O sistema está em vigor conforme as datas abaixo."
    elif st.expirada:
        msg = (
            "Licença registrada, porém o prazo de vigência encerrou. "
            "Informe novamente o serial para renovar o período nesta máquina."
        )
    elif st.registrada and not st.integridade_ok:
        msg = "Licença registrada, porém os dados não conferem. Contate o suporte técnico."
    else:
        msg = "Não foi possível concluir a ativação. Verifique o serial e tente novamente."
    return LicencaAtivarOut(
        ativa=st.ativa,
        mensagem=msg,
        data_ativacao=st.data_ativacao,
        data_expiracao=st.data_expiracao,
    )
