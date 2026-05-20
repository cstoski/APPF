from __future__ import annotations

from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.runtime_paths import get_assinaturas_dir
from app.models.sys_models import ConfigAPPF
from app.schemas.sys_schemas import ConfigAPPFOut, ConfigSalvarOut, ConfigValidacaoOut
from app.services.config_validacao_service import validar_configuracao
from app.services.email_log_service import log_teste_smtp
from app.services.seguranca_service import cifrar, get_current_username, require_roles

router = APIRouter(prefix="/api/v1/appf", tags=["APPF"])

ASSIN_DIR = get_assinaturas_dir()

ALLOWED_EXT = {".png", ".jpg", ".jpeg"}


def _logar_teste_smtp_validacao(operador: str, cfg: ConfigAPPF, validacao: dict) -> None:
    if validacao.get("escopo") not in ("email", "tudo"):
        return
    for item in validacao.get("itens", []):
        if item.get("campo") == "smtp_conexao":
            log_teste_smtp(
                operador,
                bool(item.get("ok")),
                str(item.get("mensagem", "")),
                (cfg.smtp_host or "").strip(),
            )
            break


def _salvar_assinatura(file: UploadFile, prefix: str) -> str:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="Formato de assinatura inválido. Use PNG/JPG.")
    fname = f"{prefix}_{uuid4().hex}{ext}"
    dest = ASSIN_DIR / fname
    content = file.file.read()
    with open(dest, "wb") as f:
        f.write(content)
    return f"/static/assinaturas/{fname}"


def _criar_config_vazia() -> ConfigAPPF:
    return ConfigAPPF(
        razao_social="",
        cnpj="",
        endereco="",
        nome_presidente="",
        caminho_assinatura_presidente="",
        nome_tesoureiro="",
        caminho_assinatura_tesoureiro="",
    )


def _aplicar_smtp(
    cfg: ConfigAPPF,
    *,
    smtp_host: str,
    smtp_porta: int,
    smtp_usuario: Optional[str],
    smtp_senha: Optional[str],
    smtp_usar_starttls: bool,
    smtp_remetente: str,
) -> None:
    cfg.smtp_host = smtp_host.strip() or "localhost"
    cfg.smtp_porta = smtp_porta
    cfg.smtp_usuario = smtp_usuario.strip() if smtp_usuario and smtp_usuario.strip() else None
    cfg.smtp_usar_starttls = smtp_usar_starttls
    cfg.smtp_remetente = smtp_remetente.strip() or "nao-responder@appf.local"
    if smtp_senha is not None and smtp_senha.strip():
        cfg.smtp_senha_cifrada = cifrar(smtp_senha.strip())


@router.get("", response_model=ConfigAPPFOut)
def obter_config(db: Session = Depends(get_db)) -> ConfigAPPFOut:
    cfg = db.query(ConfigAPPF).first()
    if not cfg:
        cfg = _criar_config_vazia()
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return cfg


@router.post(
    "",
    response_model=ConfigSalvarOut,
    dependencies=[Depends(require_roles("MASTER", "DEV"))],
)
def atualizar_config(
    razao_social: str = Form(...),
    cnpj: str = Form(...),
    endereco: str = Form(...),
    nome_presidente: str = Form(...),
    nome_tesoureiro: str = Form(...),
    smtp_host: str = Form(default="localhost"),
    smtp_porta: int = Form(default=587),
    smtp_usuario: Optional[str] = Form(default=None),
    smtp_senha: Optional[str] = Form(default=None),
    smtp_usar_starttls: bool = Form(default=True),
    smtp_remetente: str = Form(default="nao-responder@appf.local"),
    escopo_validacao: str = Form(default="tudo"),
    assinatura_presidente: UploadFile | None = File(default=None),
    assinatura_tesoureiro: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
) -> ConfigSalvarOut:
    cfg = db.query(ConfigAPPF).first()
    if not cfg:
        cfg = _criar_config_vazia()
        db.add(cfg)
        db.commit()
        db.refresh(cfg)

    cfg.razao_social = razao_social.strip()
    cfg.cnpj = cnpj.strip()
    cfg.endereco = endereco.strip()
    cfg.nome_presidente = nome_presidente.strip()
    cfg.nome_tesoureiro = nome_tesoureiro.strip()

    _aplicar_smtp(
        cfg,
        smtp_host=smtp_host,
        smtp_porta=smtp_porta,
        smtp_usuario=smtp_usuario,
        smtp_senha=smtp_senha,
        smtp_usar_starttls=smtp_usar_starttls,
        smtp_remetente=smtp_remetente,
    )

    if assinatura_presidente is not None:
        cfg.caminho_assinatura_presidente = _salvar_assinatura(assinatura_presidente, "presidente")

    if assinatura_tesoureiro is not None:
        cfg.caminho_assinatura_tesoureiro = _salvar_assinatura(assinatura_tesoureiro, "tesoureiro")

    db.commit()
    db.refresh(cfg)

    escopo = escopo_validacao if escopo_validacao in ("appf", "email", "tudo") else "tudo"
    validacao = validar_configuracao(cfg, escopo=escopo)
    _logar_teste_smtp_validacao(operador, cfg, validacao)
    return ConfigSalvarOut(config=cfg, validacao=validacao)


@router.post(
    "/validar",
    response_model=ConfigValidacaoOut,
    dependencies=[Depends(require_roles("MASTER", "DEV"))],
)
def validar_config_endpoint(
    escopo: str = "tudo",
    db: Session = Depends(get_db),
    operador: str = Depends(get_current_username),
):
    cfg = db.query(ConfigAPPF).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="Configuração APPF não encontrada.")
    escopo_ok = escopo if escopo in ("appf", "email", "tudo") else "tudo"
    validacao = validar_configuracao(cfg, escopo=escopo_ok)
    _logar_teste_smtp_validacao(operador, cfg, validacao)
    return validacao
