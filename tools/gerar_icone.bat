@echo off
cd /d "%~dp0\.."
python -m pip install pillow --quiet
python tools\gerar_icone.py %*
if errorlevel 1 exit /b 1
echo.
echo Pronto. Recompile com build\build_exe.bat ou build\build_installer.bat
pause
