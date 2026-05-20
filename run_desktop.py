#!/usr/bin/env python3
"""
Inicia o ZELO (API + interface web) para testes ou executável empacotado.

Uso desenvolvimento:
  python run_desktop.py

Após build:
  dist\\ZELO\\ZELO.exe
"""
from __future__ import annotations

import argparse
import os
import sys
import threading
import time
import webbrowser


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _carregar_secret_local() -> None:
    if os.environ.get("APPF_LICENSE_SECRET", "").strip():
        return
    from app.runtime_paths import get_license_secret_file

    path = get_license_secret_file()
    if path.is_file():
        linha = path.read_text(encoding="utf-8").strip().splitlines()[0].strip()
        if linha:
            os.environ["APPF_LICENSE_SECRET"] = linha


def main() -> int:
    parser = argparse.ArgumentParser(description="ZELO - Contribuições APPF (desktop)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true", help="Não abrir o navegador")
    args = parser.parse_args()

    _carregar_secret_local()

    import app.main  # noqa: F401 — garante empacotamento PyInstaller

    import uvicorn

    url = f"http://{args.host}:{args.port}"

    if not args.no_browser:

        def _abrir_navegador() -> None:
            time.sleep(2.0)
            webbrowser.open(url)

        threading.Thread(target=_abrir_navegador, daemon=True).start()

    if not _is_frozen():
        print(f"ZELO em execução: {url}")
        print("Feche esta janela ou pressione Ctrl+C para encerrar.")
        print("Dados locais: pasta 'data' ao lado do programa.")

    run_kwargs: dict = {
        "app": "app.main:app",
        "host": args.host,
        "port": args.port,
    }

    if _is_frozen():
        from app.runtime_paths import get_logs_dir

        log_file = get_logs_dir() / "zelo.log"
        run_kwargs["log_config"] = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s %(levelname)s %(name)s: %(message)s",
                },
            },
            "handlers": {
                "file": {
                    "class": "logging.FileHandler",
                    "filename": str(log_file),
                    "encoding": "utf-8",
                    "formatter": "default",
                },
            },
            "loggers": {
                "uvicorn": {"handlers": ["file"], "level": "INFO", "propagate": False},
                "uvicorn.error": {"handlers": ["file"], "level": "INFO", "propagate": False},
                "uvicorn.access": {"handlers": ["file"], "level": "INFO", "propagate": False},
            },
            "root": {"handlers": ["file"], "level": "WARNING"},
        }
    else:
        run_kwargs["log_level"] = "info"

    try:
        uvicorn.run(**run_kwargs)
    except KeyboardInterrupt:
        if not _is_frozen():
            print("\nEncerrado.")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
