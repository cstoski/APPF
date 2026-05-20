"""Bandeja do sistema (Windows) para o executável ZELO."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from typing import Callable, Optional

_shutdown_cb: Optional[Callable[[], None]] = None
_abrir_navegador_flag = threading.Event()
_status_dialog_lock = threading.Lock()
_host = "127.0.0.1"
_port = 8765

CREATE_NO_WINDOW = 0x08000000


def configurar_desktop_tray(
    *,
    host: str,
    port: int,
    on_shutdown: Callable[[], None],
) -> None:
    global _shutdown_cb, _host, _port
    _host = host
    _port = port
    _shutdown_cb = on_shutdown


def solicitar_abrir_navegador() -> None:
    _abrir_navegador_flag.set()


def url_base() -> str:
    return f"http://{_host}:{_port}"


def _icone_tray():
    from PIL import Image

    candidatos = []
    if getattr(sys, "frozen", False):
        candidatos.append(Path(sys.executable).resolve().parent / "ZeloAppfIco.ico")
    candidatos.append(Path(__file__).resolve().parents[1] / "ZeloAppfIco.ico")
    for path in candidatos:
        if path.is_file():
            img = Image.open(path)
            return img.resize((64, 64), Image.Resampling.LANCZOS)
    return Image.new("RGBA", (64, 64), (70, 130, 220, 255))


def _fetch_status() -> dict:
    req = urllib.request.Request(f"{url_base()}/api/v1/desktop/status")
    with urllib.request.urlopen(req, timeout=3) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _abrir_navegador() -> None:
    webbrowser.open(url_base())


def _texto_status(st: dict) -> str:
    linhas = [
        "ZELO - Contribuicoes APPF",
        "",
        "Servicos:",
        f"  - API: {st.get('api', '?')}",
        f"  - Interface web: {st.get('interface_web', '?')}",
        f"  - Banco de dados: {st.get('banco_dados', '?')}",
        f"  - Licenca: {st.get('licenca', '?')}",
        "",
        f"Usuarios conectados: {st.get('usuarios_conectados', 0)}",
    ]
    usuarios = st.get("usuarios") or []
    if usuarios:
        linhas.append("  - " + ", ".join(usuarios))
    else:
        linhas.append("  - (nenhum nas ultimas 5 min)")
    linhas.extend(["", url_base()])
    return "\n".join(linhas)


def _vbs_quote(texto: str) -> str:
    return '"' + texto.replace('"', '""') + '"'


def _vbs_cstr(texto: str) -> str:
    linhas = texto.replace("\r", "").split("\n")
    return " & vbCrLf & ".join(_vbs_quote(linha) for linha in linhas)


def _messagebox_ctypes_processo(titulo: str, mensagem: str) -> None:
    """MessageBoxW em processo filho (desenvolvimento, sem VBScript)."""
    import multiprocessing as mp

    def _exibir(t: str, m: str) -> None:
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, m, t, 0x1040)

    ctx = mp.get_context("spawn")
    proc = ctx.Process(target=_exibir, args=(titulo, mensagem))
    proc.start()
    proc.join(timeout=120)


def _messagebox_vbs(titulo: str, mensagem: str) -> None:
    """MsgBox via wscript em UTF-16 (executavel empacotado)."""
    vbs = f"MsgBox {_vbs_cstr(mensagem)}, 4160, {_vbs_quote(titulo)}"
    fd, path = tempfile.mkstemp(suffix=".vbs", prefix="zelo_status_")
    try:
        os.write(fd, b"\xff\xfe" + vbs.encode("utf-16-le"))
        os.close(fd)
        subprocess.run(
            ["wscript.exe", "//nologo", path],
            creationflags=CREATE_NO_WINDOW,
            timeout=120,
            check=False,
        )
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def _messagebox_info(titulo: str, mensagem: str) -> None:
    """
    Exibe dialogo em processo separado (evita deadlock com o loop da bandeja).
    """
    if sys.platform == "win32":
        if not getattr(sys, "frozen", False):
            try:
                _messagebox_ctypes_processo(titulo, mensagem)
                return
            except Exception:
                pass
        _messagebox_vbs(titulo, mensagem)
        return
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        messagebox.showinfo(titulo, mensagem, parent=root)
        root.update()
        root.destroy()
    except Exception:
        raise


def _exibir_status_worker(icon) -> None:
    if not _status_dialog_lock.acquire(blocking=False):
        return
    titulo = "ZELO - Status"
    try:
        try:
            st = _fetch_status()
            texto = _texto_status(st)
        except Exception as exc:
            texto = f"ZELO\n\nNão foi possível obter o status:\n{exc}"
        _messagebox_info(titulo, texto)
    except Exception:
        try:
            icon.notify("Não foi possível exibir o status.", title="ZELO")
        except Exception:
            pass
    finally:
        _status_dialog_lock.release()


def _mostrar_status(icon, _item) -> None:
    # Retorna imediatamente para não bloquear o menu da bandeja.
    threading.Thread(target=_exibir_status_worker, args=(icon,), daemon=True).start()


def _encerrar(icon, _item) -> None:
    icon.visible = False
    icon.stop()
    if _shutdown_cb:
        _shutdown_cb()
    os._exit(0)


def _loop_abrir_navegador(icon) -> None:
    while icon.visible:
        if _abrir_navegador_flag.wait(timeout=1.0):
            _abrir_navegador_flag.clear()
            try:
                _abrir_navegador()
            except Exception:
                pass


def executar_bandeja() -> None:
    import pystray

    # Não atualizar icon.title em thread secundária — trava o ícone no Windows.
    menu = pystray.Menu(
        pystray.MenuItem("Abrir ZELO no navegador", lambda i, _: _abrir_navegador()),
        pystray.MenuItem("Status e serviços…", _mostrar_status),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Encerrar ZELO", _encerrar),
    )
    icon = pystray.Icon(
        "ZELO",
        _icone_tray(),
        "ZELO — Contribuições APPF (clique direito)",
        menu,
    )
    threading.Thread(target=_loop_abrir_navegador, args=(icon,), daemon=True).start()
    icon.run()


def servidor_ja_ativo(host: str, port: int) -> bool:
    try:
        url = f"http://{host}:{port}/ping"
        with urllib.request.urlopen(url, timeout=2) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def sinalizar_instancia_existente(host: str, port: int) -> bool:
    """Pede à instância em execução que abra o navegador."""
    if not servidor_ja_ativo(host, port):
        return False
    try:
        url = f"http://{host}:{port}/api/v1/desktop/abrir-navegador"
        req = urllib.request.Request(url, data=b"", method="POST")
        urllib.request.urlopen(req, timeout=3)
        return True
    except (urllib.error.URLError, TimeoutError, OSError):
        webbrowser.open(f"http://{host}:{port}")
        return True
