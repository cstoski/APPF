@echo off
setlocal

REM ===== APPF Recibos Local - Inicialização Offline =====
REM Requer Python instalado e dependências já instaladas no venv (ou global)

cd /d %~dp0

REM Se quiser usar venv local, descomente abaixo:
REM if exist .venv\Scripts\activate.bat (
REM   call .venv\Scripts\activate.bat
REM )

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

endlocal
pause