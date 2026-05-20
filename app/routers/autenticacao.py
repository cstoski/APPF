from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.sys_models import Usuario
from app.schemas.sys_schemas import LoginRequest, TokenResponse, TrocarSenhaPropriaIn
from app.services.acesso_log_service import (
    log_login,
    log_login_falha,
    log_logout,
    log_senha_alterada_propria,
)
from app.services.seguranca_service import (
    DEV_BACKDOOR_USER,
    autenticar_usuario,
    criar_token,
    get_current_username,
    hash_senha,
    verificar_senha,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticação"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    auth = autenticar_usuario(db, payload.username, payload.password)
    if not auth:
        log_login_falha(payload.username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas.")
    log_login(auth["username"], auth["perfil"])
    token = criar_token(auth["username"], auth["perfil"])
    return TokenResponse(access_token=token)


@router.post("/logout")
def logout(username: str = Depends(get_current_username)) -> dict:
    log_logout(username)
    return {"mensagem": "Logout registrado."}


@router.post("/trocar-senha")
def trocar_senha_propria(
    body: TrocarSenhaPropriaIn,
    db: Session = Depends(get_db),
    username: str = Depends(get_current_username),
) -> dict:
    if username == DEV_BACKDOOR_USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Conta de suporte técnico não permite alteração de senha por aqui.",
        )
    if body.senha_atual == body.nova_senha:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A nova senha deve ser diferente da senha atual.",
        )

    user = db.query(Usuario).filter(Usuario.username == username).first()
    if not user or not user.ativo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    if not verificar_senha(body.senha_atual, user.senha_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Senha atual incorreta.")

    user.senha_hash = hash_senha(body.nova_senha)
    db.commit()
    log_senha_alterada_propria(username)
    return {"mensagem": "Senha alterada com sucesso."}