@echo off
setlocal

REM ===== APPF Recibos Local - Inicialização Offline =====
REM Requer Python instalado e dependências já instaladas no venv (ou global)

cd /d %~dp0

REM Chave de assinatura de licencas (mesma usada em tools/gerar_licenca.py)
set "APPF_LICENSE_SECRET=W93PV99093ZJONC7EIUH6SJAXI898UK5SVZJ"

REM Se quiser usar venv local, descomente abaixo:
REM if exist .venv\Scripts\activate.bat (
REM   call .venv\Scripts\activate.bat
REM )

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

endlocal
pause