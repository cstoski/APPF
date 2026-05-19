from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.schemas.sys_schemas import LoginRequest, TokenResponse
from app.services.seguranca_service import autenticar_usuario, criar_token

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticação"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    auth = autenticar_usuario(db, payload.username, payload.password)
    if not auth:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas.")
    token = criar_token(auth["username"], auth["perfil"])
    return TokenResponse(access_token=token)