@echo off
setlocal
cd /d %~dp0

REM Chave de assinatura de licencas (mesma usada em tools/gerar_licenca.py)
set "APPF_LICENSE_SECRET=W93PV99093ZJONC7EIUH6SJAXI898UK5SVZJ"

echo.
echo ===== APPF - modo rede (celular / outro PC na mesma Wi-Fi) =====
echo.

for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
  set "IP=%%a"
  goto :ip_ok
)
:ip_ok
set IP=%IP: =%

echo IP deste computador (use no celular): %IP%
echo.
echo Interface web:  http://%IP%:5173
echo API (opcional): http://%IP%:8000/docs
echo.
echo Celular e PC precisam estar na MESMA rede Wi-Fi.
echo Se nao abrir, libere as portas 5173 e 8000 no Firewall do Windows.
echo.

start "APPF API" cmd /k python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
timeout /t 2 /nobreak >nul
cd frontend
start "APPF Web" cmd /k npm run dev

endlocal
pause
