from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.sys_models import ConfigAPPF
from app.schemas.sys_schemas import ConfigAPPFOut
from app.services.seguranca_service import require_roles

router = APIRouter(prefix="/api/v1/appf", tags=["APPF"])


ASSIN_DIR = Path(__file__).resolve().parents[1] / "static" / "assinaturas"
ASSIN_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXT = {".png", ".jpg", ".jpeg"}


def _salvar_assinatura(file: UploadFile, prefix: str) -> str:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="Formato de assinatura inválido. Use PNG/JPG.")
    fname = f"{prefix}_{uuid4().hex}{ext}"
    dest = ASSIN_DIR / fname
    content = file.file.read()
    with open(dest, "wb") as f:
        f.write(content)
    # Caminho relativo para servir via /static/...
    return f"/static/assinaturas/{fname}"


@router.get("", response_model=ConfigAPPFOut)
def obter_config(db: Session = Depends(get_db)) -> ConfigAPPFOut:
    cfg = db.query(ConfigAPPF).first()
    if not cfg:
        cfg = ConfigAPPF(
            razao_social="",
            cnpj="",
            endereco="",
            nome_presidente="",
            caminho_assinatura_presidente="",
            nome_tesoureiro="",
            caminho_assinatura_tesoureiro="",
        )
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


@router.post("", response_model=ConfigAPPFOut, dependencies=[Depends(require_roles("MASTER", "DEV"))])
def atualizar_config(
    razao_social: str = Form(...),
    cnpj: str = Form(...),
    endereco: str = Form(...),
    nome_presidente: str = Form(...),
    nome_tesoureiro: str = Form(...),
    assinatura_presidente: UploadFile | None = File(default=None),
    assinatura_tesoureiro: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
) -> ConfigAPPFOut:
    cfg = db.query(ConfigAPPF).first()
    if not cfg:
        cfg = ConfigAPPF(
            razao_social="",
            cnpj="",
            endereco="",
            nome_presidente="",
            caminho_assinatura_presidente="",
            nome_tesoureiro="",
            caminho_assinatura_tesoureiro="",
        )
        db.add(cfg)
        db.commit()
        db.refresh(cfg)

    cfg.razao_social = razao_social.strip()
    cfg.cnpj = cnpj.strip()
    cfg.endereco = endereco.strip()
    cfg.nome_presidente = nome_presidente.strip()
    cfg.nome_tesoureiro = nome_tesoureiro.strip()

    if assinatura_presidente is not None:
        cfg.caminho_assinatura_presidente = _salvar_assinatura(assinatura_presidente, "presidente")

    if assinatura_tesoureiro is not None:
        cfg.caminho_assinatura_tesoureiro = _salvar_assinatura(assinatura_tesoureiro, "tesoureiro")

    db.commit()
    db.refresh(cfg)
    return cfg