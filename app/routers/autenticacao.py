from fastapi import APIRouter, Depends, HTTPException
from ..schemas.sys_schemas import AuthRequest, TokenResponse
from ..services import seguranca_service

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(payload: AuthRequest):
    # placeholder: in real implementation validate user and password
    if payload.username == "admin" and payload.password == "admin":
        token = seguranca_service.create_access_token({"sub": payload.username}, secret="devsecret")
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Credenciais inválidas")
