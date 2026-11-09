@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv .venv
    if errorlevel 1 goto erro
)
set "VGAMEPAD_SKIP_VIGEMBUS_INSTALL=true"
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto erro
echo.
echo Instalacao concluida. Abra iniciar.bat.
echo O envio real exige o driver ViGEmBus. Consulte README.md.
pause
exit /b 0
:erro
echo.
echo Falha na instalacao. Verifique Python 3.10+ e sua conexao.
pause
exit /b 1
