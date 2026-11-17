@echo off
cd /d "%~dp0"

set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo No se encontro .venv. Intentando con Python del sistema...
    set "PYTHON_EXE=python"
)

echo Iniciando servidor Django...
"%PYTHON_EXE%" manage.py migrate
if errorlevel 1 (
    echo Error al ejecutar migraciones.
    pause
    exit /b 1
)

echo Abriendo navegador...
timeout /t 3 >nul
start "" http://127.0.0.1:8000

"%PYTHON_EXE%" manage.py runserver 0.0.0.0:8000

pause
