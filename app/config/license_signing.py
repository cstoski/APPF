from __future__ import annotations

import os
from app.runtime_paths import get_install_root, get_license_secret_file


def obter_chave_assinatura_licenca() -> bytes:
    """
    Chave usada para gerar/validar serial.
    Ordem: APPF_LICENSE_SECRET > license_secret.local (pasta do exe) > tools/ (dev) > chave dev.
    """
    raw = (os.environ.get("APPF_LICENSE_SECRET") or "").strip()
    for candidate in (
        get_license_secret_file(),
        get_install_root() / "tools" / "license_secret.local",
    ):
        if not raw and candidate.is_file():
            raw = candidate.read_text(encoding="utf-8").strip().splitlines()[0].strip()
            break
    if not raw:
        raw = "APPF-DEV-ALTERE-APPF_LICENSE_SECRET-ANTES-DE-PRODUCAO"
    return raw.encode("utf-8")
