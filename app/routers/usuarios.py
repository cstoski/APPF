from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.sys_models import Usuario
from app.schemas.sys_schemas import UsuarioCreate, UsuarioOut, UsuarioUpdate
from app.services.seguranca_service import hash_senha, require_roles, get_current_username

router = APIRouter(prefix="/api/v1/usuarios", tags=["Usuários"])


@router.get("", response_model=list[UsuarioOut], dependencies=[Depends(require_roles("MASTER", "DEV"))])
def listar_usuarios(db: Session = Depends(get_db)) -> list[UsuarioOut]:
    return db.query(Usuario).order_by(Usuario.id.asc()).all()


@router.post("", response_model=UsuarioOut, dependencies=[Depends(require_roles("MASTER", "DEV"))])
def criar_usuario(data: UsuarioCreate, db: Session = Depends(get_db)) -> UsuarioOut:
    if db.query(Usuario).filter(Usuario.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username já existe.")
    u = Usuario(
        username=data.username,
        senha_hash=hash_senha(data.password),
        perfil=data.perfil,
        ativo=data.ativo,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@router.put("/{user_id}", response_model=UsuarioOut, dependencies=[Depends(require_roles("MASTER", "DEV"))])
def atualizar_usuario(user_id: int, data: UsuarioUpdate, db: Session = Depends(get_db)) -> UsuarioOut:
    u = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    if data.password:
        u.senha_hash = hash_senha(data.password)
    if data.perfil is not None:
        u.perfil = data.perfil
    if data.ativo is not None:
        u.ativo = data.ativo
    db.commit()
    db.refresh(u)
    return u


@router.post("/{user_id}/desativar", response_model=UsuarioOut, dependencies=[Depends(require_roles("MASTER", "DEV"))])
def desativar_usuario(user_id: int, db: Session = Depends(get_db), _me: str = Depends(get_current_username)) -> UsuarioOut:
    u = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    u.ativo = False
    db.commit()
    db.refresh(u)
    return u