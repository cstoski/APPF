from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException

from app.models.sys_models import ConfigAPPF
from app.services.seguranca_service import decifrar


@dataclass
class SmtpSettings:
    host: str
    porta: int
    usuario: Optional[str]
    senha: Optional[str]
    usar_starttls: bool
    remetente: str


def obter_smtp_da_config(cfg: ConfigAPPF) -> SmtpSettings:
    return SmtpSettings(
        host=(cfg.smtp_host or "localhost").strip(),
        porta=int(cfg.smtp_porta or 587),
        usuario=(cfg.smtp_usuario or "").strip() or None,
        senha=decifrar(cfg.smtp_senha_cifrada) if cfg.smtp_senha_cifrada else None,
        usar_starttls=bool(cfg.smtp_usar_starttls),
        remetente=(cfg.smtp_remetente or "nao-responder@appf.local").strip(),
    )


def validar_smtp_configurado(smtp: SmtpSettings) -> None:
    if not smtp.host:
        raise HTTPException(
            status_code=400,
            detail="Configure o servidor SMTP em Configuração > E-mail.",
        )
    if not smtp.remetente:
        raise HTTPException(
            status_code=400,
            detail="Informe o e-mail remetente em Configuração > E-mail.",
        )
