"""Endpoints locais para bandeja do sistema e segunda instância do executável."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import text
from app.config.database import SessionLocal, engine
from app.services.sessao_ativa_service import contar_usuarios_conectados, listar_usuarios_conectados
from app.services.licenca_service import montar_status_licenca

router = APIRouter(prefix="/api/v1/desktop", tags=["Desktop"])


def _exigir_cliente_local(request: Request) -> None:
    host = (request.client.host if request.client else "") or ""
    if host not in ("127.0.0.1", "::1", "localhost"):
        raise HTTPException(status_code=403, detail="Acesso permitido apenas no computador local.")


@router.get("/status")
def status_desktop(request: Request) -> dict:
    _exigir_cliente_local(request)
    usuarios = listar_usuarios_conectados()
    licenca_msg = "não verificada"
    try:
        db = SessionLocal()
        try:
            st = montar_status_licenca(db)
            if st.ativa:
                licenca_msg = "ativa"
            elif st.expirada:
                licenca_msg = "expirada"
            elif st.registrada:
                licenca_msg = "registrada (inativa)"
            else:
                licenca_msg = "não ativada"
        finally:
            db.close()
    except Exception:
        licenca_msg = "erro ao consultar"

    banco_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        banco_ok = True
    except Exception:
        pass

    return {
        "servidor": "ativo",
        "api": "ativa",
        "interface_web": "ativa",
        "banco_dados": "ok" if banco_ok else "indisponível",
        "licenca": licenca_msg,
        "usuarios_conectados": len(usuarios),
        "usuarios": usuarios,
    }


@router.post("/abrir-navegador")
def abrir_navegador(request: Request) -> dict:
    _exigir_cliente_local(request)
    from app.desktop_tray import solicitar_abrir_navegador

    solicitar_abrir_navegador()
    return {"ok": True, "mensagem": "Navegador será aberto."}
