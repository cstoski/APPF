"""
Caminhos para desenvolvimento e executável (PyInstaller).
Dados graváveis ficam na pasta do .exe (data/, logs/, banco).
"""
from __future__ import annotations

import sys
from pathlib import Path


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


def get_static_dir() -> Path:
    """Pasta gravável de arquivos estáticos (assinaturas, etc.)."""
    if is_frozen():
        path = get_install_root() / "static"
    else:
        path = get_app_dir() / "static"
    path.mkdir(parents=True, exist_ok=True)
    if is_frozen():
        _sync_bundled_static(path)
    return path


def _sync_bundled_static(dest: Path) -> None:
    """Copia recursos empacotados na primeira execução (sem sobrescrever uploads)."""
    origem = get_bundle_root() / "app" / "static"
    if not origem.is_dir():
        return
    import shutil

    for item in origem.rglob("*"):
        if not item.is_file():
            continue
        rel = item.relative_to(origem)
        alvo = dest / rel
        if not alvo.is_file():
            alvo.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, alvo)


def get_assinaturas_dir() -> Path:
    path = get_static_dir() / "assinaturas"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_frontend_dist_dir() -> Path:
    if is_frozen():
        return get_bundle_root() / "frontend" / "dist"
    return get_install_root() / "frontend" / "dist"


def get_license_secret_file() -> Path:
    return get_install_root() / "license_secret.local"
