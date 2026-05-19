import subprocess
import platform


def get_hwid_windows() -> str:
    """Try to extract HWID on Windows via WMIC."""
    if platform.system() != "Windows":
        return ""
    try:
        output = subprocess.check_output(["wmic", "csproduct", "get", "uuid"])  # may require permissions
        text = output.decode(errors="ignore").splitlines()
        if len(text) >= 2:
            return text[1].strip()
    except Exception:
        pass
    return ""


def validar_serial(hwid: str, serial: str) -> bool:
    # placeholder validation logic
    return hwid != "" and serial.endswith(hwid[-4:])
