"""
Caminhos para desenvolvimento e executável (PyInstaller).
Dados graváveis ficam na pasta do .exe (data/, logs/, banco).
Assinaturas (presidente/tesoureiro) são cadastro — apenas em data/assinaturas/.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

_PREFIXO_ASSINATURA_URL = "/static/assinaturas/"
_EXT_ASSINATURA = {".png", ".jpg", ".jpeg"}


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def get_install_root() -> Path:
    """Pasta do instalador / projeto (gravável)."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def get_bundle_root() -> Path:
    """Recursos empacotados (_MEIPASS) ou raiz do projeto."""
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", str(get_install_root())))
    return get_install_root()


def get_app_dir() -> Path:
    if is_frozen():
        return get_bundle_root() / "app"
    return Path(__file__).resolve().parent


def get_data_dir() -> Path:
    if is_frozen():
        path = get_install_root() / "data"
    else:
        path = get_app_dir() / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_logs_dir() -> Path:
    path = get_data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_assinaturas_dir() -> Path:
    """Imagens de assinatura enviadas no cadastro APPF (não vão no executável)."""
    path = get_data_dir() / "assinaturas"
    path.mkdir(parents=True, exist_ok=True)
    return path


def nome_arquivo_de_caminho_assinatura(caminho: str | None) -> str:
    if not (caminho or "").strip():
        return ""
    rel = str(caminho).strip().replace("\\", "/")
    if rel.startswith(_PREFIXO_ASSINATURA_URL):
        rel = rel[len(_PREFIXO_ASSINATURA_URL) :]
    elif rel.startswith("static/assinaturas/"):
        rel = rel[len("static/assinaturas/") :]
    return rel.lstrip("/")


def caminho_publico_assinatura(nome_arquivo: str) -> str:
    return f"{_PREFIXO_ASSINATURA_URL}{nome_arquivo.lstrip('/')}"


def resolver_arquivo_assinatura(caminho: str | None) -> Path | None:
    nome = nome_arquivo_de_caminho_assinatura(caminho)
    if not nome:
        return None
    alvo = get_assinaturas_dir() / nome
    return alvo if alvo.is_file() else None


def migrar_assinaturas_legadas() -> None:
    """Move assinaturas antigas (app/static ou pasta static do exe) para data/assinaturas."""
    dest = get_assinaturas_dir()
    origens: list[Path] = [
        get_app_dir() / "static" / "assinaturas",
        get_install_root() / "static" / "assinaturas",
    ]
    if is_frozen():
        bundle = get_bundle_root() / "app" / "static" / "assinaturas"
        if bundle.is_dir():
            origens.append(bundle)

    vistos: set[Path] = set()
    for origem in origens:
        try:
            origem_res = origem.resolve()
        except OSError:
            continue
        if not origem.is_dir() or origem_res in vistos or origem_res == dest.resolve():
            continue
        vistos.add(origem_res)
        for item in origem.iterdir():
            if not item.is_file() or item.suffix.lower() not in _EXT_ASSINATURA:
                continue
            alvo = dest / item.name
            if not alvo.is_file():
                shutil.copy2(item, alvo)


def get_frontend_dist_dir() -> Path:
    if is_frozen():
        return get_bundle_root() / "frontend" / "dist"
    return get_install_root() / "frontend" / "dist"


def get_license_secret_file() -> Path:
    return get_install_root() / "license_secret.local"
