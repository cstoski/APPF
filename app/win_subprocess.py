"""Subprocessos no Windows sem abrir janela de console."""
from __future__ import annotations

import subprocess
import sys
from typing import Sequence

CREATE_NO_WINDOW = 0x08000000
STARTF_USESHOWWINDOW = 0x00000001
SW_HIDE = 0


def check_output_oculto(args: Sequence[str], *, timeout: float | None = 15) -> str:
    """Executa comando e retorna stdout como texto, sem janela de prompt."""
    kwargs: dict = {
        "stderr": subprocess.STDOUT,
        "text": True,
        "timeout": timeout,
        "shell": False,
    }
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = SW_HIDE
        kwargs["startupinfo"] = startupinfo
        kwargs["creationflags"] = CREATE_NO_WINDOW
    return subprocess.check_output(list(args), **kwargs)
