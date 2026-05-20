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


def _aguardar_servidor(host: str, port: int, timeout: float = 30.0) -> bool:
    from app.desktop_tray import servidor_ja_ativo

    fim = time.time() + timeout
    while time.time() < fim:
        if servidor_ja_ativo(host, port):
            return True
        time.sleep(0.3)
    return False


def _run_uvicorn_thread(host: str, port: int, run_kwargs: dict) -> None:
    import uvicorn

    uvicorn.run(**run_kwargs)


def _run_com_bandeja(host: str, port: int, run_kwargs: dict, abrir_browser: bool) -> int:
    import uvicorn
    from app.desktop_tray import (
        configurar_desktop_tray,
        executar_bandeja,
        sinalizar_instancia_existente,
        url_base,
    )

    if sinalizar_instancia_existente(host, port):
        return 0

    config = uvicorn.Config(**run_kwargs)
    server = uvicorn.Server(config)

    def _parar_servidor() -> None:
        server.should_exit = True

    configurar_desktop_tray(host=host, port=port, on_shutdown=_parar_servidor)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    if not _aguardar_servidor(host, port):
        print("ZELO: servidor não respondeu a tempo.")
        return 1

    if abrir_browser:
        webbrowser.open(url_base())

    executar_bandeja()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="ZELO - Contribuições APPF (desktop)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true", help="Não abrir o navegador")
    parser.add_argument(
        "--tray",
        action="store_true",
        help="Bandeja do sistema (padrão no executável Windows)",
    )
    args = parser.parse_args()

    _carregar_secret_local()

    import app.main  # noqa: F401 — garante empacotamento PyInstaller

    url = f"http://{args.host}:{args.port}"
    usar_bandeja = args.tray or _is_frozen()

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

    if usar_bandeja and sys.platform == "win32":
        return _run_com_bandeja(args.host, args.port, run_kwargs, abrir_browser=not args.no_browser)

    if not args.no_browser:

        def _abrir_navegador() -> None:
            time.sleep(2.0)
            webbrowser.open(url)

        threading.Thread(target=_abrir_navegador, daemon=True).start()

    if not _is_frozen():
        print(f"ZELO em execução: {url}")
        print("Feche esta janela ou pressione Ctrl+C para encerrar.")
        print("Dados locais: pasta 'data' ao lado do programa.")

    try:
        import uvicorn

        uvicorn.run(**run_kwargs)
    except KeyboardInterrupt:
        if not _is_frozen():
            print("\nEncerrado.")
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
