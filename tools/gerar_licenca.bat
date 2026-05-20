@echo off
setlocal EnableExtensions
cd /d "%~dp0\.."

set "APPF_LICENSE_SECRET=W93PV99093ZJONC7EIUH6SJAXI898UK5SVZJ"

set "HWID=%~1"
if "%HWID%"=="" (
  echo.
  echo ===== Gerar serial de licenca APPF =====
  echo.
  set /p "HWID=Cole o HWID exibido na tela do cliente: "
)

if "%HWID%"=="" (
  echo ERRO: HWID nao informado.
  goto :fim
)

echo.
echo Gerando serial para este equipamento...
echo.

python "%~dp0gerar_licenca.py" --hwid "%HWID%"
set "ERR=%ERRORLEVEL%"

if not "%ERR%"=="0" (
  echo.
  echo ERRO ao gerar (codigo %ERR%^). Verifique se o Python esta instalado e se esta na pasta do projeto.
)

:fim
echo.
pause
endlocal
