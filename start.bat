@echo off
chcp 65001 >nul
title Patoruzú Stats

echo.
echo  ==========================================
echo   PATORUZÚ STATS — Iniciando...
echo  ==========================================
echo.

:: ── 1. Buscar Python (en PATH o en rutas típicas de instalación) ──────────
set PYTHON=

python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON=python
    goto :python_found
)

for %%p in (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%PROGRAMFILES%\Python313\python.exe"
    "%PROGRAMFILES%\Python312\python.exe"
    "%PROGRAMFILES%\Python311\python.exe"
    "%PROGRAMFILES(X86)%\Python313\python.exe"
    "%PROGRAMFILES(X86)%\Python312\python.exe"
    "%PROGRAMFILES(X86)%\Python311\python.exe"
) do (
    if exist %%p (
        set PYTHON=%%p
        goto :python_found
    )
)

:: ── Python no encontrado — descargar e instalar automáticamente ───────────
echo  Python no está instalado. Instalando automáticamente...
echo  Esto puede tardar unos minutos. Por favor esperá.
echo.

:: Verificar que haya conexión a internet
ping -n 1 python.org >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Sin conexión a internet.
    echo  Conectate a internet y volvé a abrir la app.
    echo.
    pause
    exit /b 1
)

:: Descargar installer de Python 3.13 con PowerShell
set PYINSTALLER=%TEMP%\python_installer.exe
echo  Descargando Python...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe' -OutFile '%PYINSTALLER%'" >nul 2>&1
if not exist "%PYINSTALLER%" (
    echo  [ERROR] No se pudo descargar Python.
    echo  Intentar de nuevo o descargarlo manualmente desde:
    echo  https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: Instalar silenciosamente (pide UAC una sola vez)
echo  Instalando Python — Windows puede pedir permiso, hacer clic en Si.
"%PYINSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
if errorlevel 1 (
    echo  [ERROR] No se pudo instalar Python.
    echo  Intentar de nuevo o descargarlo manualmente desde:
    echo  https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
del "%PYINSTALLER%" >nul 2>&1
echo  [OK] Python instalado correctamente

:: Refrescar PATH para que python quede disponible en esta sesión
set PYTHON=%LOCALAPPDATA%\Programs\Python\Python313\python.exe
if not exist "%PYTHON%" set PYTHON=%PROGRAMFILES%\Python313\python.exe

:python_found
:: ── 2. Verificar versión mínima 3.11 ──────────────────────────────────────
for /f "tokens=2 delims= " %%v in ('"%PYTHON%" --version 2^>^&1') do set PYVER=%%v
for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do (
    set PYMAJOR=%%a
    set PYMINOR=%%b
)
if %PYMAJOR% LSS 3 goto :version_error
if %PYMAJOR% EQU 3 if %PYMINOR% LSS 11 goto :version_error
echo  [OK] Python %PYVER%
goto :check_port

:version_error
echo  [ERROR] Se requiere Python 3.11 o superior. Versión instalada: %PYVER%
echo  Descargar desde: https://www.python.org/downloads/
echo.
pause
exit /b 1

:: ── 3. Verificar puerto 8000 libre ────────────────────────────────────────
:check_port
netstat -an 2>nul | find "0.0.0.0:8000" >nul
if not errorlevel 1 (
    echo.
    echo  [AVISO] Patoruzú Stats ya está corriendo.
    echo  Abriendo el navegador...
    echo.
    timeout /t 2 >nul
    start http://localhost:8000
    pause
    exit /b 0
)

:: ── 4. Crear entorno virtual si no existe ─────────────────────────────────
if not exist "venv\" (
    echo  Preparando la app por primera vez, esto tarda un minuto...
    "%PYTHON%" -m venv venv
    if errorlevel 1 (
        echo  [ERROR] No se pudo preparar el entorno de la app.
        pause
        exit /b 1
    )
)

:: ── 5. Activar entorno virtual ────────────────────────────────────────────
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo  [ERROR] No se pudo activar el entorno de la app.
    pause
    exit /b 1
)

:: ── 6. Instalar/actualizar dependencias ───────────────────────────────────
echo  Verificando dependencias...
pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 (
    echo  [ERROR] No se pudieron instalar los componentes necesarios.
    echo  Verificar conexión a internet e intentar de nuevo.
    pause
    exit /b 1
)
echo  [OK] Todo listo

:: ── 7. Abrir navegador y arrancar servidor ────────────────────────────────
echo.
echo  Iniciando Patoruzú Stats...
echo  Para cerrar la app, cerrá esta ventana.
echo.
timeout /t 2 >nul
start http://localhost:8000
uvicorn main:app --host 0.0.0.0 --port 8000

pause
