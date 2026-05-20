#!/usr/bin/env python3
"""
Gera serial de licença offline vinculado ao HWID (uma licença por computador).

Uso:
  tools/gerar_licenca.bat
  tools/gerar_licenca.bat HWID-DO-CLIENTE
  python tools/gerar_licenca.py --hwid HWID-DO-CLIENTE

Chave: APPF_LICENSE_SECRET ou arquivo tools/license_secret.local
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config.license_signing import _SECRET_FILE, obter_chave_assinatura_licenca
from app.services.licenca_serial_service import VALIDADE_DIAS, gerar_serial_para_hwid


def _status_chave() -> str:
    if (os.environ.get("APPF_LICENSE_SECRET") or "").strip():
        return "variavel APPF_LICENSE_SECRET"
    if _SECRET_FILE.is_file():
        return f"arquivo {_SECRET_FILE.name}"
    return "chave de desenvolvimento (NAO use em producao)"


def main() -> None:
    parser = argparse.ArgumentParser(description="Gerar serial de licença APPF por HWID")
    parser.add_argument("--hwid", default="", help="HWID exibido na tela de licença do cliente")
    parser.add_argument(
        "--data-emissao",
        default="",
        help="Data de emissão ISO (AAAA-MM-DD). Padrão: hoje",
    )
    args = parser.parse_args()

    hwid = (args.hwid or "").strip()
    if not hwid:
        try:
            hwid = input("Cole o HWID do cliente: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nCancelado.", file=sys.stderr)
            sys.exit(1)

    if not hwid:
        print("ERRO: informe o HWID (copie da tela Configuracao > Licenca do cliente).", file=sys.stderr)
        sys.exit(1)

    emissao = date.today()
    if args.data_emissao:
        try:
            emissao = date.fromisoformat(args.data_emissao)
        except ValueError:
            print("ERRO: data-emissao invalida. Use AAAA-MM-DD.", file=sys.stderr)
            sys.exit(1)

    obter_chave_assinatura_licenca()
    serial = gerar_serial_para_hwid(hwid, emissao)

    print()
    print("========== SERIAL GERADO ==========")
    print(serial)
    print("===================================")
    print()
    print(f"HWID:     {hwid}")
    print(f"Emissao:  {emissao.isoformat()}")
    print(f"Validade: {VALIDADE_DIAS} dias")
    print(f"Chave:    {_status_chave()}")
    print()
    print("No cliente: login MASTER > cole o serial na tela de licenca > Ativar.")


if __name__ == "__main__":
    main()
