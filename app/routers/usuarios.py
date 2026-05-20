from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.sys_models import Usuario
from app.schemas.sys_schemas import UsuarioCreate, UsuarioOut, UsuarioUpdate
from app.services.acesso_log_service import (
    log_senha_alterada_admin,
    log_usuario_alterar,
    log_usuario_criar,
    log_usuario_desativar,
)
from app.services.seguranca_service import hash_senha, require_roles, get_current_username

router = APIRouter(prefix="/api/v1/usuarios", tags=["Usuários"])


def _bloquear_admin_sistema(u: Usuario) -> None:
    if u.username == "admin" and u.perfil == "MASTER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="O usuário master do sistema não pode ser alterado por esta tela.",
        )


def _detalhes_alteracao_usuario(u: Usuario, data: UsuarioUpdate) -> str:
    partes: list[str] = []
    if data.username is not None:
        novo = data.username.strip()
        if novo and novo != u.username:
            partes.append(f"username: {u.username} -> {novo}")
    if data.perfil is not None and data.perfil != u.perfil:
        partes.append(f"perfil: {u.perfil} -> {data.perfil}")
    if data.password:
        partes.append("senha=redefinida")
    if data.ativo is not None and data.ativo != u.ativo:
        partes.append(f"ativo: {u.ativo} -> {data.ativo}")
    return " | ".join(partes) if partes else "campos=sem mudança registrada"


def _validar_perfil_cadastro(perfil: str) -> None:
    if perfil not in ("OPERADOR", "MASTER"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Perfil inválido. Use OPERADOR ou MASTER.",
        )


@router.get("", response_model=list[UsuarioOut], dependencies=[Depends(require_roles("MASTER", "DEV"))])
def listar_usuarios(db: Session = Depends(get_db)) -> list[UsuarioOut]:
    return (
        db.query(Usuario)
        .filter(Usuario.username != "admin")
        .order_by(Usuario.username.asc())
        .all()
    )


@router.post("", response_model=UsuarioOut, dependencies=[Depends(require_roles("MASTER", "DEV"))])
def criar_usuario(
    data: UsuarioCreate,
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
) -> UsuarioOut:
    username = data.username.strip()
    if username == "admin":
        raise HTTPException(status_code=400, detail="Este nome de usuário é reservado ao sistema.")
    _validar_perfil_cadastro(data.perfil)
    if db.query(Usuario).filter(Usuario.username == username).first():
        raise HTTPException(status_code=400, detail="Username já existe.")
    u = Usuario(
        username=username,
        senha_hash=hash_senha(data.password),
        perfil=data.perfil,
        ativo=data.ativo,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    log_usuario_criar(operador, u.username, u.perfil)
    return u


@router.put("/{user_id}", response_model=UsuarioOut, dependencies=[Depends(require_roles("MASTER", "DEV"))])
def atualizar_usuario(
    user_id: int,
    data: UsuarioUpdate,
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
) -> UsuarioOut:
    u = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    _bloquear_admin_sistema(u)
    alvo_antes = u.username
    detalhes = _detalhes_alteracao_usuario(u, data)
    if data.username is not None:
        novo = data.username.strip()
        if not novo:
            raise HTTPException(status_code=400, detail="Nome de usuário inválido.")
        if novo == "admin":
            raise HTTPException(status_code=400, detail="Este nome de usuário é reservado ao sistema.")
        if novo != u.username and db.query(Usuario).filter(Usuario.username == novo).first():
            raise HTTPException(status_code=400, detail="Nome de usuário já existe.")
        u.username = novo
    if data.password:
        u.senha_hash = hash_senha(data.password)
    if data.perfil is not None:
        _validar_perfil_cadastro(data.perfil)
        u.perfil = data.perfil
    if data.ativo is not None:
        u.ativo = data.ativo
    db.commit()
    db.refresh(u)
    log_usuario_alterar(operador, alvo_antes if alvo_antes != u.username else u.username, detalhes)
    if data.password:
        log_senha_alterada_admin(operador, u.username)
    return u


@router.post("/{user_id}/desativar", response_model=UsuarioOut, dependencies=[Depends(require_roles("MASTER", "DEV"))])
def desativar_usuario(
    user_id: int,
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
) -> UsuarioOut:
    u = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    _bloquear_admin_sistema(u)
    u.ativo = False
    db.commit()
    db.refresh(u)
    log_usuario_desativar(operador, u.username)
    return u
